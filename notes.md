staffing co:
- IT domain 

staffing co reach out to customers 
- 3 customers TCS, Infy, Wipro

Personas:
account manager / AE for each customer - deals with all jobs for that customers
- for large companies, multiple AM (per division or teams or orgs)

AM will have multiple recruiters under AM
(recruter for small customers)

AM can work with multiple Hiring Manager (HM)
AM m::n HM relationship
AM does round robin to assign recruiter for HM
AM can also be a recruiter

company can have one or more organizations
organization is SaaS tenant -> user management is per organization

USER MANAGEMENT
  - OPEN ID connect + OAuth based 
  - super user per organization 

- workflow/process
AM (Staffco) co-ordinates reaches out to Hiring Manager (HM) (TCS)


Job requirement process can be initiated from AM/HM

HM -> portal or call or email
StaffingCo can have a client portal
  -> enter job details and save it
  -> HM can track it - see and review applicants 

AM -> assign recruiter 
AM also have additional responsibilities in furture roadmap/features

Recruiter -> 
will have multiple job requests (HM -> AM -> Recruiter)
candidates sourced from internal database, available resoruces, job boards or sub-vendors
Reviews Candidates and shortlist them as applications to a job

Source: internal database 
  - searching canddiates based on strcutured filters, classic search ex: location, experience, travel
    - search will provide 50000 candidates
    - quick review
    - smart review 
Feature: Feature to support quick review and smart review
AI USP: value for recruiter for AI assisted candidate search to get shortlist/applicants

Source: Job boards
Fearture: continuously monitor and review the applications in the job board
Recruiter will submit the reviwed applications to job request (visible in client portal)

Recruiter will schedule the interviews

After interview, the selected applicant will be placed
  -> as contract (contract with client)
  -> as temporary (defined time period with client, per task ex: consultant in workshop or surgeon)
  -> as permanent hire to customers (TCS)

MVP scope is to target until placements -> a.k.a Front office

CLIENT PORTAL
- Build the client portal - job is created in client portal. How do we notify account manager
- Support job requests via email -> reflect in the client portal, should be stored in backend/database 
- How can AM assign jobs to recruiter
- How can recruiter post the jobs in job boards?
- provide integration with job boards
- provide feature to post jobs in clien't own website

CANDIDATE PORTAL
- we should have our own candidate portal which customers will embed in their website. 
  - if someone applies for TCS, their website will embed and redirect candidates to candidate portal 
- feature: candidate a profile and upload resume
- feature: candidate can edit or update profile and upload new updated resume
- feature: search feature for candidate to search for jobs
- feature: setup alert for a job based on set criteria 
- feature: send notification / email for matched jobs
- feature: show list of jobs applied
- feature: show list of interviews, integrate with google calendar

- AI USP feature: To extract or parse resumes from email or other sources and create a candidate in the system
- AI USP feature: candidate profile strength and recommendations


RECRUITER TARGETS:
- goals/KPI - monthly & yearly job closure, number of candidates interactions
- KPI: consider factors such as gross margin = bill_rate * total number of hours - burden (expenses, meals, travel)
- feature: activity tracking to support recruit KPI

IDEAS
- can we learn about candidates based on feedback from HM/Recruiter
- can we capture interview feedbacks from HM
- can we provide interview questions for HM
- bot should dynamically interview the candidate -> multi-turn or deep dive questions -> prvoide a candidate interview score
- fraud detection
- resume red flagging (AI bloated)


ATS is an agent
- how and where does agent skills fit in this AI feature / architecture? Do we have one agent skill per  domain such as IT or healthcare? one per HM
- how and where does MCP fit in this AI feature / architecture?
- AG UI 
- agent understand the user - learns about HM/Recruiter
- voice to text feature


