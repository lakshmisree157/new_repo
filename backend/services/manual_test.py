import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.reminder_service import send_reminder_email

if __name__ == '__main__':
    test_email = "klakshmisree1573@gmail.com"
    print(f"--- Manual SendGrid Test ---")
    print(f"Target Email: {test_email}")
    
    # You can change the name and dog name for the test here
    send_reminder_email(
        adopter_email=test_email, 
        adopter_name="Lakshmi Sree", 
        dog_name="Test Buddy"
    )
    
    print(f"--- Test Execution Finished ---")
    print(f"Check the console output above for status codes.")
    print(f"If successful (Status 202), please check your inbox (and spam folder) at {test_email}.")
