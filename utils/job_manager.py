"""
Track download jobs and their status
"""
import uuid
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class Job:
    """Download job tracking"""
    job_id: str
    input_type: str
    input_value: str
    status: str  # queued, downloading, completed, failed
    total_tracks: int = 0
    completed_tracks: int = 0
    failed_tracks: int = 0
    error_messages: List[str] = None
    output_directory: str = ""
    created_at: str = ""
    completed_at: Optional[str] = None
    failed_track_details: List[Dict] = None
    
    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []
        if self.failed_track_details is None:
            self.failed_track_details = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def update_from_result(self, result: Dict):
        """Update job from download result"""
        self.total_tracks = result.get('total', 0)
        self.completed_tracks = result.get('completed', 0)
        self.failed_tracks = result.get('failed', 0)
        self.failed_track_details = result.get('failed_tracks', [])
        
        if result.get('errors'):
            self.error_messages.extend(result['errors'])
        
        if result.get('output_dir'):
            self.output_directory = result['output_dir']
        
        # Determine final status
        if self.completed_tracks > 0:
            if self.failed_tracks == 0:
                self.status = 'completed'
            else:
                self.status = 'completed_with_errors'
        else:
            self.status = 'failed'
        
        self.completed_at = datetime.now().isoformat()


class JobManager:
    """Manage download jobs"""
    
    def __init__(self, jobs_file: str = "jobs.json"):
        self.jobs_file = jobs_file
        self.jobs: Dict[str, Job] = {}
        self.load_jobs()
    
    def create_job(self, input_type: str, input_value: str) -> Job:
        """Create a new job"""
        job = Job(
            job_id=str(uuid.uuid4()),
            input_type=input_type,
            input_value=input_value,
            status='queued'
        )
        self.jobs[job.job_id] = job
        self.save_jobs()
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        return self.jobs.get(job_id)
    
    def update_job(self, job: Job):
        """Update a job"""
        self.jobs[job.job_id] = job
        self.save_jobs()
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs"""
        return list(self.jobs.values())
    
    def save_jobs(self):
        """Save jobs to file"""
        try:
            with open(self.jobs_file, 'w') as f:
                jobs_dict = {job_id: job.to_dict() for job_id, job in self.jobs.items()}
                json.dump(jobs_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving jobs: {e}")
    
    def load_jobs(self):
        """Load jobs from file"""
        if not os.path.exists(self.jobs_file):
            return
        
        try:
            with open(self.jobs_file, 'r') as f:
                jobs_dict = json.load(f)
                for job_id, job_data in jobs_dict.items():
                    self.jobs[job_id] = Job(**job_data)
        except Exception as e:
            print(f"Error loading jobs: {e}")
    
    def save_failed_tracks_csv(self, job: Job):
        """Save failed tracks to CSV"""
        if not job.failed_track_details:
            return
        
        csv_filename = f"failed_tracks_{job.job_id}.csv"
        csv_path = os.path.join("logs", csv_filename)
        
        os.makedirs("logs", exist_ok=True)
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['artist', 'title', 'error'])
                writer.writeheader()
                writer.writerows(job.failed_track_details)
            
            print(f"Failed tracks saved to: {csv_path}")
        except Exception as e:
            print(f"Error saving failed tracks CSV: {e}")