# Student-Timetable-System
## ✨ Key Features

- **Centralized Management:** Create, edit, and manage all student and faculty schedules from a single, user-friendly desktop application.

- **Dynamic Timetable Generation:** Instantly generate and display specific timetables based on various criteria:
  - 🎓 **By Academic Level:** View the complete schedule for any specific level or department.
  - 👨‍🏫 **By Faculty Member:** Display an individual professor's full schedule. Includes an intelligent feature to **consolidate schedules** for professors teaching across multiple faculties into a single, unified view.
  - 📍 **By Location:** Instantly view the schedule for any classroom, lab, or lecture hall (e.g., Hall 5).

- **Conflict Resolution:** Built-in logic to help identify and prevent scheduling conflicts.

- **Universal Print Function:** A flexible print option is available for **any** generated timetable, allowing for easy creation of hard copies for distribution.
## 📸 Screenshots

![Main Dashboard](https://github.com/Heba-Rajab/Student-Timetable-System/blob/main/1.png)

![Creating Groups](https://github.com/Heba-Rajab/Student-Timetable-System/blob/main/2.png)

![Entering Timetables](https://github.com/Heba-Rajab/Student-Timetable-System/blob/main/3.png)

![Timetable View](https://github.com/Heba-Rajab/Student-Timetable-System/blob/main/4.png)

![Entering Data](https://github.com/Heba-Rajab/Student-Timetable-System/blob/main/7.png)

![Server Setting](https://github.com/Heba-Rajab/Student-Timetable-System/blob/main/11.png)
## 💻 My Core Contributions

As the **Lead Developer**,  I voluntarily took on the responsibility for the entire core of the project. My primary role was to **architect and develop the main body of the program from the ground up, and single-handedly solve all of the application's complex scheduling and conflicting problems.** I saw this project as a crucial opportunity to push my limits and grow under pressure. It was a challenging and rewarding experience that allowed me to simulate a real-world work environment, which was my personal goal.

My contributions can be broken down as follows:

### 1. UI/UX Design & Implementation
- **From Concept to Code:** I initiated the design process by sketching wireframes on paper and led team discussions on color theory, resulting in the selection of a clean and professional navy-and-white theme.
- **Tkinter Development:** I single-handedly translated these designs into a fully functional and responsive user interface using Tkinter. This was my first time undertaking a project of this scale, and I overcame numerous challenges by leveraging critical thinking and extensive research, significantly enhancing my problem-solving skills.

### 2. Complex Problem-Solving & Algorithm Development
Driven by the core challenges outlined by our project supervisor, I took the lead in developing solutions for the most complex scheduling issues:
- **Cross-Department Conflict Resolution:** I engineered the core logic to resolve a critical issue where a single professor teaching the same course to two different departments could cause a scheduling conflict.
- **Unified Faculty Schedule Generation:** I devised a practical solution to display a professor's complete timetable, even when they teach across different faculties. This was achieved by architecting the system to handle data from multiple faculties seamlessly.
- **Handling Practical Sessions (Labs):** I researched and attempted a solution for scheduling practical sessions for two different groups at the same time, exploring JSON-based approaches. *(This feature is currently in the experimental phase).*

### 3. Development of Key Application Pages
I was the **sole developer** for three of the five primary pages, handling both the front-end design and the back-end logic from scratch:
- **Groups & Courses Setup Page:** I built the interface for administrators to define "groups" (a combination of department, level, course,labs and professor), which forms the foundational data for all scheduling.
- **Timetable Entry Page:** This was the most challenging page. I developed the complex grid interface for timetable entry and implemented the logic to prevent data conflicts in cells, time slots, and locations.
- **Timetable Viewing Page:** I designed and programmed a dynamic dashboard with four main frames: a general view for any selected timetable, a dedicated view for a professor's schedule, a view for a specific location's schedule, and a universal print button that generates a PDF of the currently displayed table.

### 4. Database Integration
- I utilized the **pyodbc** library to establish the connection between the Python application and the SQL Server database. I was responsible for writing and managing all the SQL queries executed from the application (SELECT, INSERT, UPDATE, etc.), ensuring seamless and reliable data flow.

---
*(Full details of my entire process, including the conflict resolution algorithms, are available in the provided documentation file.)*

## 👥 Team & Roles

This project was a collaborative effort. The roles were distributed as follows:

- **Heba Ragab**: **Lead Developer & System Architect**
  - *Led the end-to-end development, from conceptual design to core logic and deployment oversight.*

- **Lobna Hesham**: **Database Architect**
  - *Designed and implemented the database schema using MS SQL Server.*

- **Nermeen Saad**: **UI Developer & Deployment Specialist**
  - *Developed the "Data Management" and "Settings" pages and handled the final application deployment.*

## 🛠️ Technologies Used

- **Language:** Python
- **GUI:** Tkinter
- **Database:** SQL Server
- **Connectivity:** pyodbc

## 🚀 How to Run the Project

1.  **Restore the Database:**
    - Ensure you have Microsoft SQL Server and SSMS installed.
    - In SSMS, right-click on the "Databases" folder and choose "Restore Database...".
    - Select "Device" as the source, and then locate and select the `.bak` file from this repository.
    - Click "OK" to restore the database.
2.  **Configure the Connection:**
    - Open the Python file containing the database connection string and update it with your server name and credentials.
3.  **Run the Application:**
    - Run the `main.py` file: `python main.py`
