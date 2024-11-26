import os
import pandas as pd
import tempfile
import json
from collections import defaultdict
from pymongo import MongoClient
from copydetect import CopyDetector
from tqdm import tqdm


# MongoDB connection setup
MONGO_URI= os.getenv("MONGO_URI")
DATABASE_NAME = "Weekly-Contest-410"
COLLECTION_NAME = ""


# Define the submission class
class Submission:
    def __init__(self, username, userslug, contest_rank, question_id, language, code, submission_id):
        self.username = username
        self.userslug = userslug
        self.contest_rank = contest_rank
        self.question_id = question_id
        self.language = language
        self.code = code
        self.submission_id = submission_id


# Load submissions from CSV
def load_submissions_from_csv(file_path):
    df = pd.read_csv(file_path)
    submissions = []
    for _, row in df.iterrows():
        submissions.append(Submission(
            username=row['username'],
            userslug=row['userslug'],
            contest_rank=row['contest_rank'],
            question_id=row['question_id'],
            language=row['language'],
            code=row['code'],
            submission_id=row['submission_id']
        ))
    return submissions


# Group submissions by question and language
def group_submissions(submissions):
    grouped_submissions = defaultdict(lambda: defaultdict(list))
    for submission in submissions:
        grouped_submissions[submission.question_id][submission.language].append(submission)
    return grouped_submissions


# Process a group of submissions (plagiarism detection)
def process_group(submissions, language):
    plagiarism_pairs = []
    if len(submissions) < 2:
        return plagiarism_pairs
    
    with tempfile.TemporaryDirectory() as tmpdir:
        submission_file_map = {}
        for submission in submissions:
            file_path = os.path.join(tmpdir, f"{submission.submission_id}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(submission.code)
            submission_file_map[file_path] = submission
        
        detector = CopyDetector(
            test_dirs=[tmpdir],
            extensions=[".txt"],
            force_language=language,
            silent=True
        )
        detector.run()
        
        copied = detector.get_copied_code_list()
        for sim1, sim2, file1, file2, _, _, _ in copied:
            # if sim1 > 0.8 and sim2 > 0.8:
            sub1 = submission_file_map[file1]
            sub2 = submission_file_map[file2]
            plagiarism_pairs.append({
                "plagiarist": sub1.username,
                "plagiarist_user_id": sub1.userslug,
                "plagiarized_from": sub2.username,
                "plagiarized_from_user_id": sub2.userslug,
                "plagiarist_submission_id": sub1.submission_id,
                "plagiarized_submission_id": sub2.submission_id,
                "plagiarist_rank": sub1.contest_rank,
                "plagiarized_rank": sub2.contest_rank,
                "confidence_score": min(sim1, sim2) * 100,
                "language": language
            })
    return plagiarism_pairs


# Process all questions and languages
def process_all_submissions(submissions):
    grouped_submissions = group_submissions(submissions)
    plagiarism_results = []

    # Add tqdm progress bar here for the outer loop over questions and languages
    for question_id, languages in tqdm(grouped_submissions.items(), desc="Processing Questions", unit="question"):
        for language, subs in tqdm(languages.items(), desc=f"Processing Language {question_id}", unit="language"):
            plagiarism_pairs = process_group(subs, language)
            for plagiarism in plagiarism_pairs:
                plagiarism["question_id"] = question_id
                plagiarism_results.append(plagiarism)
    
    return plagiarism_results


# Save plagiarism results to MongoDB
def save_to_mongodb(plagiarism_results):
    try:
        client = MongoClient(MONGO_URI)
        db = client['leetcode_contests']  # Use a single database 'leetcode_contests'
        
        if plagiarism_results:
            # Group results by question_id
            grouped_results = {}
            for result in plagiarism_results:
                question_id = result["question_id"]
                if question_id not in grouped_results:
                    grouped_results[question_id] = []
                grouped_results[question_id].append(result)
            
            # Save each group's results to its respective collection (named by question_id)
            for question_id, results in tqdm(grouped_results.items(), desc="Saving to MongoDB", unit="collection"):
                collection_name = str(question_id)  # Collection name is the question_id itself
                collection = db[collection_name]
                collection.insert_many(results)
                print(f"Successfully saved {len(results)} records to MongoDB collection '{collection_name}'.")
        else:
            print("No plagiarism results to save.")
    except Exception as e:
        print(f"Error while saving to MongoDB: {e}")
    finally:
        client.close()

# Load the contest_slug from the file created by data_acquisition.py
def load_contest_slug():
    try:
        with open("data/submissions_data/contest_slug.json", "r") as file:
            data = json.load(file)
            return data.get("contest_slug")
    except FileNotFoundError:
        print("contest_slug.json not found. Please make sure data_acquisition.py ran first.")
        exit(1)


def main():
    contest_slug = load_contest_slug()
    # Load submissions from CSV
    submissions = load_submissions_from_csv('data/submissions_data/' + 'contest_slug' + '.csv')
    
    # Process submissions and detect plagiarism
    plagiarism_results = process_all_submissions(submissions)
    
    # Save results to MongoDB
    save_to_mongodb(plagiarism_results)

if __name__ == "__main__":
    main()
