# CS319---Group-11-Term-Project
# TA Management System

## Overview
The *TA Management System* is a web-based platform designed to efficiently manage Teaching Assistant (TA) duties and proctoring assignments. It ensures fair workload distribution, allows for task tracking, and automates the proctoring assignment process.

## Features

###  *Primary Functionalities*
- *TA Duty Tracking*:  
  - TAs log their tasks such as lab work, grading, recitations, and office hours.
  - Course instructors receive notifications and can approve or reject task submissions.
  - Approved tasks contribute to the TA’s total workload for the semester.
  
- *Proctoring Assignment*:  
  - Assigns proctoring duties prioritizing TAs with the least workload.
  - Ensures fair workload distribution while respecting various constraints such as academic level, leave requests, and scheduling conflicts.

###  *Secondary Functionalities*
- *TA Leave of Absence Management*:  
  - TAs can request leave for conferences, medical reasons, or vacations.
  - Requests must be approved by the department chair or authorized staff.
  - Approved leave prevents the TA from being assigned to proctoring duties during those dates.

- *Proctoring Assignment Methods*:  
  - *Automatic Assignment*:
    - Assigns TAs based on their current workload.
    - Prioritizes TAs from the same department or course.
    - Takes into account restrictions such as TA leave, academic level, and exam conflicts.
    - If no suitable TAs are found, administrators can override restrictions or request additional TAs from other departments.
  - *Manual Assignment*:
    - Staff can manually assign proctors from a sorted list of available TAs.
    - Provides warnings if assigning TAs who have workload concerns or prior assignments.

- *Proctor Swap System*:  
  - TAs can request a swap with another TA within the same department.
  - The system notifies the new TA, and if accepted, the swap is finalized.
  - Authorized staff can also manually reassign proctoring duties when necessary.

- *Classroom Lists & Exam Organization*:  
  - Generates and prints student distributions for exam rooms.
  - Allows distribution to be alphabetical or randomized.

- *Reporting & Logs*:  
  - Tracks TA workload, proctoring duties, approvals, and reassignments.
  - Generates reports on total workload, proctoring assignments, and system activity.

- *System Import & Role-Based Access*:  
  - Allows importing of semester offerings, student and faculty data via Excel.
  - Supports role-based access control for TAs, faculty, department staff, and administrators.
  - Ensures that only authorized users can modify assignments, approve requests, and access specific data.
