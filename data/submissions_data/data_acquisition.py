import concurrent.futures
import csv
import json
import logging
import os
import urllib.request
from random import randint
from time import sleep
from typing import List, Tuple
from random_user_agent.params import OperatingSystem, SoftwareName
from random_user_agent.user_agent import UserAgent
from datetime import datetime
from pymongo import MongoClient

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraping/submissions")
logger.setLevel(logging.INFO)


# LeetCode API URLs
MONGO_URI= os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["leetcode_contests"]  # Database name
collection = db["contests"]  # Collection name
CONTEST_BASE_URL = "https://leetcode.com/contest"
CONTEST_API_URL = "https://leetcode.com/contest/api/ranking"
SUBMISSIONS_API_URL = "https://leetcode.com/api/submissions"
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "referer": "https://leetcode.com/contest",
}


# Limit to first 10 pages
PAGE_LIMIT = 1  # This is now set to 10 pages
NUM_WORKERS = 10  # Number of concurrent threads
MAX_RETRIES = 50  # Maximum retry attempts for failed requests
REQUEST_TIMEOUT_SEC = 15  # Timeout for requests


# Rotating user-agent setup
USER_AGENT_ROTATOR = UserAgent(
    software_names=[SoftwareName.CHROME.value, SoftwareName.FIREFOX.value],
    operating_systems=[OperatingSystem.WINDOWS.value, OperatingSystem.MACOS.value],
    limit=200,
)


# Function to make GET requests with retries and user-agent rotation
def get(url: str) -> dict:
    delay = 1
    for i in range(MAX_RETRIES):
        try:
            headers = HEADERS.copy()
            headers["user-agent"] = USER_AGENT_ROTATOR.get_random_user_agent()
            request = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SEC)
            return json.loads(response.read().decode())
        except Exception as _:
            logger.error(f"Failed to fetch {url} (try {i})")
            sleep(randint(1, delay))
            delay = min(delay * 2, 30)  # Exponential backoff for retries
    logger.error(f"Could not fetch {url} after {MAX_RETRIES} retries, exiting")
    exit(1)


# Fetch contest questions
def get_questions(contest_slug: str) -> List[dict]:
    response = get(f"{CONTEST_API_URL}/{contest_slug}/?pagination=1&region=global")
    questions = []
    for i, question in enumerate(response["questions"]):
        questions.append({
            "id": int(question["question_id"]),
            "name": question["title"],
            "number_in_contest": i + 1,
            "contest_slug": contest_slug
        })
    return questions


# Fetch the 3rd and 4th contest questions sorted by 'id'
def get_selected_questions(contest_slug: str) -> List[dict]:
    """Fetch and return the 3rd and 4th contest questions."""
    response = get(f"{CONTEST_API_URL}/{contest_slug}/?pagination=1&region=global")
    
    if "questions" not in response:
        logger.error(f"No questions found for contest {contest_slug}")
        return []
    
    questions = sorted(response["questions"], key=lambda q: q["id"])
    selected_questions = questions[2:4]  # Selecting the 3rd and 4th questions
    
    logger.info(f"Selected questions: {selected_questions}")
    return selected_questions

# Save selected questions to a CSV file and MongoDB
def save_selected_questions_to_csv_and_mongo(questions: List[dict], contest_slug: str, filename: str = "questions_data/questions.csv"):
    if not questions or len(questions) != 2:
        logger.error("Exactly 2 questions are required to save.")
        return

    # Sort questions to determine question_3 and question_4
    sorted_questions = sorted(questions, key=lambda x: int(x["id"]))
    question_3 = sorted_questions[0]["question_id"]
    question_4 = sorted_questions[1]["question_id"]

    # Save to CSV
    with open(filename, mode="w", newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id", "question_id"])
        writer.writeheader()
        for question in questions:
            writer.writerow({
                "id": question["id"],
                "question_id": question["question_id"]
            })

    logger.info(f"Selected questions saved to {filename}")

    # Prepare data for MongoDB
    contest_data = {
        "contest_name": contest_slug,
        "contest_link": f"https://leetcode.com/contest/{contest_slug}",
        "contest_date": datetime.now().strftime("%B %d, %Y, %I:%M %p"),
        "question_3": question_3,
        "question_4": question_4
    }

    # Insert into MongoDB
    try:
        collection.insert_one(contest_data)
        logger.info(f"Contest data saved to MongoDB: {contest_data}")
    except Exception as e:
        logger.error(f"Error saving to MongoDB: {e}")


# Fetch submissions for a specific contest page
def get_submissions(contest_slug: str, page: int) -> dict:
    return get(f"{CONTEST_API_URL}/{contest_slug}/?pagination={page}&region=global")


# Fetch code for a specific submission
def get_submission_with_code(submission_id: str) -> dict:
    return get(f"{SUBMISSIONS_API_URL}/{submission_id}")


# Save a single submission locally in CSV format
def save_submission(submission: dict, contest_slug: str):
    file_name: str = "submissions_data/" + contest_slug + ".csv"
    with open(file_name, "a", newline='', encoding='utf-8') as file:  # Append mode
        writer = csv.DictWriter(file, fieldnames=submission.keys())
        if file.tell() == 0:
            writer.writeheader()
        writer.writerow(submission)


# Fetch all submissions and process them
def get_all_submissions(contest_slug: str, questions: List[dict]) -> None:
    logger.info(f"Fetching submissions for contest {contest_slug}")
    question_ids = [q["id"] for q in questions]  # Filter only relevant questions
    i = 1

    while i <= PAGE_LIMIT:  # Limit to the first 10 pages
        response = get_submissions(contest_slug, i)
        if not response["submissions"]:
            break

        logger.info(f"Processing page {i}")
        page_submissions = []

        for user_submissions, user in zip(response["submissions"], response["total_rank"]):
            for question_id, submission_info in user_submissions.items():
                if int(question_id) not in question_ids:
                    continue
                if submission_info["data_region"] == "CN":
                    continue

                # Fetch the code for the submission
                submission_with_code = get_submission_with_code(submission_info["submission_id"])
                submission_data = {
                    "username": user["username"],
                    "userslug": user["user_slug"],
                    "contest_rank": user["rank"],
                    "question_id": question_id,
                    "language": submission_with_code["lang"],
                    "code": submission_with_code["code"],
                    "submission_id": submission_info["submission_id"]
                }

                # Save submission immediately after fetching
                save_submission(submission_data, contest_slug)

        logger.info(f"Fetched submissions from page {i}")
        i += 1

# Main function to handle the local scraping
def process_contest_locally():
    contest_slug = input("Enter the contest slug (e.g., weekly-contest-416): ")
    # Save the contest_slug to a JSON file so that main.py can read it
    with open("contest_slug.json", "w") as file:
        json.dump({"contest_slug": contest_slug}, file)

    # Fetch and save the 3rd and 4th questions sorted by 'id'
    logger.info(f"Fetching and saving 3rd and 4th questions for contest {contest_slug}")
    selected_questions = get_selected_questions(contest_slug)
    save_selected_questions_to_csv_and_mongo(selected_questions, contest_slug)

    # Fetch contest questions for processing submissions
    logger.info(f"Fetching all contest questions for contest {contest_slug}")
    questions = get_questions(contest_slug)

    # Fetch all submissions for the relevant questions
    logger.info(f"Fetching all submissions for contest {contest_slug}")
    get_all_submissions(contest_slug, questions)


if __name__ == "__main__":
    process_contest_locally()
