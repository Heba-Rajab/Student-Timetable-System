# coding: utf-8
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import customtkinter as ctk
import pyodbc
import subprocess
import tempfile
from PIL import ImageGrab
import os
import configparser 
import win32print
import win32api
import datetime

# Color Palette
HEADER_FRAME = "#2c3e50"
MAIN_PAGE_BUTTONS_FRAME_COLOR = "#F5F7FA"
MAIN_PAGE_BUTTONS_HOVER = "#3E546B"
ACCENT_COLOR = "#2980b9"
BACKGROUND_COLOR = "#ecf0f1"
TABLE_HEADER_COLOR = "#bdc3c7"
CELL_COLOR = "#ffffff"
HIGHLIGHT_COLOR = "#60c3af"

class BasePage(tk.Frame):
    """Base class for all pages with common functionality"""
    def __init__(self, parent, return_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.return_callback = return_callback
        self.configure(bg='#f0f0f0')

# data_manager
class DataManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.clear_data()  # تهيئة البيانات
        return cls._instance
    
    def clear_data(self):
        self.schedule_data = {}  # لحفظ الجداول
        self.groups_data = []    # لحفظ المجموعات

class GroupsCreation(BasePage):
    """Class for the schedule entry page"""
    def __init__(self, parent, return_callback):
        super().__init__(parent, return_callback)
        self.data_manager = DataManager()
        self.groups = self.data_manager.groups_data
        self.editing_group_index = None
        self.original_group_data = None
        
        # إعداد اتصال قاعدة البيانات
        self.SERVER = '.'
        self.DATABASE = 'project'
        
        # تحميل البيانات من قاعدة البيانات
        self.year_levels = self.load_year_levels_from_db()
        self.departments = self.load_departments_from_db()
        self.instructors = self.load_instructors_from_db()
        self.subjects = self.load_subjects_from_db()
         
        self.practical_groups_count_container = None
        self.practical_instructor_container = None
        self.dept_groups_count_spinboxes = {}
        
        self.setup_ui()
        self.load_groups_from_db()


    def connect_db(self):
        try:
            # الحصول على إعدادات الاتصال من الصفحة الرئيسية
            main_page = self.master.master if isinstance(self.master, tk.Toplevel) else self.master
            if hasattr(main_page, 'db_server') and hasattr(main_page, 'db_name'):
                self.SERVER = main_page.db_server
                self.DATABASE = main_page.db_name
            
            conn = pyodbc.connect(
                f'DRIVER={{SQL Server}};SERVER={self.SERVER};'
                f'DATABASE={self.DATABASE};Trusted_Connection=yes;'
            )
            return conn
        except pyodbc.Error as e:
            messagebox.showerror("خطأ في الاتصال", f"فشل الاتصال بقاعدة البيانات:\n{str(e)}")
            return None
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")
            return None
    
        
    def load_year_levels_from_db(self):
        conn = self.connect_db()
        if not conn:
            return ["الأولى", "الثانية", "الثالثة", "الرابعة"]  # قيم افتراضية في حالة فشل الاتصال
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Levels_name FROM Levels ORDER BY Levels_ID")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل المستويات: {str(e)}")
            return ["الأولى", "الثانية", "الثالثة", "الرابعة"]
        finally:
            conn.close()

    def load_departments_from_db(self):
        """تحميل الأقسام من قاعدة البيانات"""
        conn = self.connect_db()
        if not conn:
            return ["الرياضيات", "الحاسب علوم", "فيزياءوعلوم الحاسب"]
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Department_name FROM Department ORDER BY Department_ID")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل الأقسام: {str(e)}")
            return ["الرياضيات", "الحاسب علوم", "فيزياءوعلوم الحاسب"]
        finally:
            conn.close()

    def load_instructors_from_db(self):
        conn = self.connect_db()
        if not conn:
            return ['هبة', 'رجب']
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT F_name + ' ' + L_name AS Full_name FROM Lecturer ORDER BY Lecturer_ID")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل المحاضرين: {str(e)}")
            return ['هبة', 'رجب']
        finally:
            conn.close()

    def load_subjects_from_db(self):
        """تحميل المواد من قاعدة البيانات"""
        conn = self.connect_db()
        if not conn:
            return ['عربي', 'انجليزي', 'فيزياء', 'كيمياء']
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Course_name FROM Courses ORDER BY Course_ID")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل المواد: {str(e)}")
            return ['عربي', 'انجليزي', 'فيزياء', 'كيمياء']
        finally:
            conn.close()

    def setup_ui(self):
        
        # Setup use interface

        top_frame = tk.LabelFrame(
            self,
            text=" اضافة مجموعة",
            padx=10,
            pady=10,
            labelanchor='ne',
            bg="white",  # Background color
            bd=2,  # Border width
            relief=tk.SOLID,  # Border style
            fg="black",
            font=('Arial', 15)
        )
        top_frame.pack(fill="both", padx=20, pady=10, side="right")
        
        # Create a canvas and scrollbar
        canvas = tk.Canvas(top_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(top_frame, orient=tk.VERTICAL, command=canvas.yview)
    
        # Pack scrollbar first so it doesn't move
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
    
        # Create an inner frame to hold all widgets
        inner_frame = tk.Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        def configure_scrollregion(event):
            canvas.itemconfig("all", width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        
        canvas.bind("<Configure>", configure_scrollregion)
        inner_frame.bind("<Configure>", configure_scrollregion)
    
        # Department container - now in inner_frame instead of top_frame
        self.dept_container = tk.Frame(inner_frame, bg="white")
        self.dept_container.pack(fill=tk.X, padx=5, pady=5, anchor='e')

        # Department Row
        self.dept_comboboxes = []
        self.add_dept_row()

        # Add more than one department
        self.add_dept_btn = ttk.Button(inner_frame, text="إضافة قسم",command=lambda: [self.add_dept_row(), canvas.configure(scrollregion=canvas.bbox("all"))])
        # self.add_dept_btn = ttk.Button(inner_frame, text="إضافة قسم", command=self.add_dept_row)
        self.add_dept_btn.pack(pady=(0, 5), padx=5, anchor='e')

        # Year
        year_frame = tk.Frame(inner_frame, bg="white")
        year_frame.pack(fill=tk.X, pady=5)
        tk.Label(year_frame, text=": المستوي", font=('Arial Unicode MS', 12, 'bold'), bg="white").pack(side=tk.RIGHT, padx=5)
        self.year_combobox = ttk.Combobox(year_frame, values=self.year_levels, width=32, state="readonly", style="Custom.TCombobox")
        self.year_combobox.pack(side=tk.RIGHT, fill=tk.X, expand=False, padx=10)

        # Subject
        subject_frame = tk.Frame(inner_frame, bg="white")
        subject_frame.pack(fill=tk.X, pady=5)
        tk.Label(subject_frame, text=": المادة", font=('Arial Unicode MS', 12, 'bold'), bg="white").pack(side=tk.RIGHT, padx=5)
        self.subject_entry = ttk.Combobox(subject_frame, values=self.subjects, justify='right', width=32, state="readonly", style="Custom.TCombobox")
        self.subject_entry.pack(side=tk.RIGHT, fill=tk.X, expand=False, padx=25, pady=10)
    
        # lecturer
        lecturer_frame = tk.Frame(inner_frame, bg="white")
        lecturer_frame.pack(fill=tk.X, pady=5)
        tk.Label(
            lecturer_frame, 
            text=": المحاضر",
            bg="white",
            fg="black",
            font=('Arial', 12, 'bold')
        ).pack(side=tk.RIGHT, padx=5)
        self.instructor_entry = ttk.Combobox(lecturer_frame, justify='right', values=self.instructors, width=32, state='readonly', style="Custom.TCombobox")
        self.instructor_entry.pack(side=tk.RIGHT, fill=tk.X, expand=False, padx=15, pady=15)
    
        # Hours input
        self.setup_hours_inputs(inner_frame)
        
        


       # combobox style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.TCombobox",
                    padding=5)  
        

        # Adding groups control buttons
        btn_frame = tk.Frame(inner_frame,bg="white")
        btn_frame.pack(pady=5, anchor='e')

        self.add_group_btn = ttk.Button(btn_frame, text="إضافة مجموعة", command=self.add_group)
        self.add_group_btn.pack(side=tk.RIGHT, padx=5)
        
        groups_frame = tk.LabelFrame(
            self,
            text=" المجموعات الموجودة",
            bg="white",
            fg="black",
            bd=2,
            relief="solid",
            labelanchor="ne",
            padx=10, 
            pady=10,
            font=('Arial', 15)
        )
        groups_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Search bar
        search_frame = tk.Frame(groups_frame , bg="white")
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(search_frame, text=": بحث", bg="white").pack(side=tk.RIGHT, padx=5)
        self.group_search_entry = ttk.Entry(search_frame, justify='right')
        self.group_search_entry.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
        self.group_search_entry.bind("<KeyRelease>", self.filter_group_list)

        # groups list
        list_container = ttk.Frame(groups_frame)
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        self.group_listbox = tk.Listbox(
            list_container, 
            yscrollcommand=scrollbar.set,
            font=("Traditional Arabic", 14),
            justify='right',
            
        )
        self.group_listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.group_listbox.yview)

        # delete button
        btn_frame = tk.Frame(groups_frame,bg="white")
        btn_frame.pack(pady=5, anchor='e')

        delete_btn = ttk.Button(btn_frame, text="حذف المحدد", command=self.delete_group_with_warning)
        delete_btn.pack(side=tk.RIGHT, padx=5)
        
        # Return to main page button 
        back_button = ttk.Button(
            self, 
            text="العودة للرئيسية", 
            command=self.return_callback,
            style='Rounded.TButton'
        )
        back_button.pack(pady=20)
        


    def delete_group_with_warning(self):
        """عرض تحذير قبل الحذف"""
        selected = self.group_listbox.curselection()
        if not selected:
            messagebox.showerror("خطأ", "الرجاء تحديد مجموعة للحذف!")
            return
        
        index = selected[0]
        if index >= len(self.groups):
            return
        
        group_to_delete = self.groups[index]
        
        # عرض تحذير عام أولاً
        warning_msg = "سيتم حذف هذه المجموعة من قاعدة البيانات وجميع الجداول المرتبطة بها!\n"
        warning_msg += f"المادة: {group_to_delete['subject']}\n"
        warning_msg += f"المحاضر: {group_to_delete['instructor']}\n"
        warning_msg += f"النوع: {'نظرية' if group_to_delete['Group_Type'] == 'lecture' else 'عملي'}"
        
        if group_to_delete['Group_Type'] == 'practical':
            warning_msg += f" (المجموعة {group_to_delete.get('group_number', 1)})"
        
        if messagebox.askyesno("تحذير مهم", warning_msg + "\n\nهل تريد الاستمرار في الحذف؟"):
            self.delete_group()
            
    def setup_hours_inputs(self, parent_frame):
        # spinbox style
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("Large.TSpinbox", 
                    padding=4,
                    arrowsize=15,
                    bordercolor="gray",  # Add border for better visibility
                    relief="solid",      # Border style
                    font=('Arial', 10)) # Ensures consistent text size

        hours_frame = tk.Frame(parent_frame, bg="white")
        hours_frame.pack(fill=tk.X, pady=5)

        # theory hours
        theory_frame = tk.Frame(hours_frame, bg="white")
        theory_frame.pack(side=tk.RIGHT, padx=5)
        tk.Label(theory_frame, text=" ساعات النظري", font=('Arial Unicode MS', 11, 'bold'), bg="white").pack(side=tk.RIGHT)
        self.theory_hours = ttk.Spinbox(theory_frame, from_=1, to=10, width=5, style="Large.TSpinbox")
        self.theory_hours.set(1)
        self.theory_hours.pack(side=tk.RIGHT, padx=5)

        # practical hours
        practical_frame = tk.Frame(hours_frame, bg="white")
        practical_frame.pack(side=tk.RIGHT, padx=5)
        tk.Label(practical_frame, text=" ساعات العملي", font=('Arial Unicode MS', 11, 'bold'), bg="white").pack(side=tk.RIGHT)
        self.practical_hours = ttk.Spinbox(practical_frame, from_=0, to=4, width=5, style="Large.TSpinbox")
        self.practical_hours.set(0)
        self.practical_hours.pack(side=tk.RIGHT)

        # تم إزالة حقل عدد المجموعات العام (practical_groups_count) لأنه لم يعد مستخدمًا
        # حيث تم استبداله بعدد مجموعات لكل قسم في dept_groups_count_spinboxes

        # ربط الأحداث
        self.practical_hours.bind("<KeyRelease>", self.toggle_practical_fields)
        self.practical_hours.bind("<ButtonRelease>", self.toggle_practical_fields)

    def toggle_practical_fields(self, event=None):
        # التحقق من وجود الحاويات
        if not hasattr(self, 'practical_groups_count_container') or not hasattr(self, 'practical_instructor_container'):
            return

        # إخفاء الحاويات القديمة
        self.practical_groups_count_container.pack_forget()
        for widget in self.practical_groups_count_container.winfo_children():
            widget.destroy()
        
        self.practical_instructor_container.pack_forget()
        for widget in self.practical_instructor_container.winfo_children():
            widget.destroy()

        try:
            practical_hours = int(self.practical_hours.get())
            if practical_hours > 0:
                current_instructors = self.load_instructors_from_db()
                
                # إنشاء واجهة عدد المجموعات لكل قسم
                tk.Label(
                    self.practical_groups_count_container,
                    text="عدد المجموعات العملي لكل قسم:",
                    bg="white",
                    font=('Arial Unicode MS', 11, 'bold')
                ).pack(anchor='e', padx=5, pady=5)
                
                groups_count_frame = tk.Frame(self.practical_groups_count_container, bg="white")
                groups_count_frame.pack(fill=tk.X, padx=5, pady=5, anchor='e')
                
                self.dept_groups_count_spinboxes = {}
                
                for dept_cb in self.dept_comboboxes:
                    dept = dept_cb.get()
                    if not dept:
                        continue
                    
                    dept_frame = tk.Frame(groups_count_frame, bg="white")
                    dept_frame.pack(fill=tk.X, pady=2, anchor='e')
                    
                    tk.Label(dept_frame, text=f"{dept}:", bg="white").pack(side=tk.RIGHT, padx=5)
                    spinbox = ttk.Spinbox(dept_frame, from_=1, to=20, width=5, style="Large.TSpinbox")
                    spinbox.set(1)
                    spinbox.pack(side=tk.RIGHT, padx=5)
                    self.dept_groups_count_spinboxes[dept] = spinbox
                
                self.practical_groups_count_container.pack(fill=tk.X, pady=5)
                
                for spinbox in self.dept_groups_count_spinboxes.values():
                    spinbox.bind("<KeyRelease>", lambda e: self.update_practical_instructors_ui(current_instructors))
                    spinbox.bind("<ButtonRelease>", lambda e: self.update_practical_instructors_ui(current_instructors))
                
                self.update_practical_instructors_ui(current_instructors)
        
        except ValueError:
            self.practical_groups_count_container.pack_forget()
            self.practical_instructor_container.pack_forget()

    # دالة جديدة: تحديث واجهة محاضري العملي
    def update_practical_instructors_ui(self, instructors_list):
        for widget in self.practical_instructor_container.winfo_children():
            widget.destroy()
        
        for dept, spinbox in self.dept_groups_count_spinboxes.items():
            try:
                groups_count = int(spinbox.get())
            except ValueError:
                groups_count = 1
            
            dept_frame = tk.LabelFrame(
                self.practical_instructor_container,
                text=f"محاضر العملي - {dept}",
                padx=5,
                pady=5,
                bg="white", 
                fg="black",
                bd=2,
                relief="solid",
                labelanchor="ne", 
                font=('Arial', 10)
            )
            dept_frame.pack(fill=tk.X, pady=5, padx=5, anchor='e')
            
            for group_num in range(1, groups_count + 1):
                group_frame = tk.Frame(dept_frame, bg="white")
                group_frame.pack(fill=tk.X, pady=2)
                
                tk.Label(group_frame, text=f"محاضر المجموعة {group_num}:", bg="white").pack(side=tk.RIGHT, padx=5)
                entry = ttk.Combobox(group_frame, values=instructors_list, state="readonly", width=32, style="Custom.TCombobox")
                entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        self.practical_instructor_container.pack(fill=tk.X, pady=5)

    def get_practical_instructors(self):
        practical_instructors = {}
        try:
            if int(self.practical_hours.get()) > 0:
                # لكل قسم في dept_groups_count_spinboxes
                for dept, spinbox in self.dept_groups_count_spinboxes.items():
                    try:
                        groups_count = int(spinbox.get())
                    except ValueError:
                        groups_count = 1
                    
                    practical_instructors[dept] = []
                    
                    # البحث عن إطار القسم المناسب
                    found = False
                    for dept_frame in self.practical_instructor_container.winfo_children():
                        if isinstance(dept_frame, tk.LabelFrame) and dept_frame.cget('text').endswith(dept):
                            found = True
                            entry_frames = [child for child in dept_frame.winfo_children() if isinstance(child, tk.Frame)]
                            
                            for group_num in range(groups_count):
                                if group_num < len(entry_frames):
                                    entry = entry_frames[group_num].winfo_children()[1]  # حقل Combobox
                                    instructor = entry.get().strip()
                                    if not instructor: 
                                        raise ValueError(f"يجب إدخال محاضر العملي للمجموعة {group_num+1} في قسم {dept}")
                                    
                                    if instructor not in self.instructors:
                                        raise ValueError(f"المحاضر {instructor} غير موجود في قائمة المحاضرين")
                                        
                                    practical_instructors[dept].append(instructor)
                                else:
                                    practical_instructors[dept].append("")
                            break
                    
                    if not found:
                        raise ValueError(f"لم يتم العثور على واجهة المحاضرين للقسم {dept}")
        
        except (ValueError, IndexError) as e:
            raise ValueError(str(e))
        
        return practical_instructors

    # def add_group(self):
    #     """إضافة مجموعة جديدة مع الربط الصحيح بين المادة والأقسام"""
    #     try:
    #         selected_depts = [cb.get() for cb in self.dept_comboboxes if cb.get()]
    #         if not selected_depts:
    #             raise ValueError("يجب اختيار قسم واحد على الأقل")

    #         year_level = self.year_combobox.get()
    #         instructor = self.instructor_entry.get().strip()
    #         subject = self.subject_entry.get().strip()
    #         theory_hours = int(self.theory_hours.get())
    #         practical_hours = int(self.practical_hours.get())
    #         practical_groups_count = int(self.practical_groups_count.get()) if practical_hours > 0 else 1

    #         if not all([year_level, instructor, subject]):
    #             raise ValueError("جميع الحقول المميزة بعلامة (*) مطلوبة")

    #         self.validate_group_uniqueness(selected_depts, year_level, subject, theory_hours, practical_hours)

    #         practical_instructors = self.get_practical_instructors() if practical_hours > 0 else {}

    #         conn = self.connect_db()
    #         if not conn:
    #             raise ValueError("فشل الاتصال بقاعدة البيانات")

    #         cursor = conn.cursor()

    #         try:
    #             cursor.execute("SELECT Course_ID FROM Courses WHERE Course_name=?", (subject,))
    #             course_id = cursor.fetchone()[0]

    #             cursor.execute("SELECT Lecturer_ID FROM Lecturer WHERE F_name + ' ' + L_name=?", (instructor,))
    #             lecturer_id = cursor.fetchone()[0]

    #             cursor.execute("SELECT Levels_ID FROM Levels WHERE Levels_name=?", (year_level,))
    #             level_id = cursor.fetchone()[0]

    #             cursor.execute("""
    #                 INSERT INTO Groups (
    #                     Department_ID, Levels_ID, Course_ID, Lecturer_ID,
    #                     Theory_Hours, Practical_Hours, Practical_Groups_Count, Group_Type
    #                 ) VALUES (?, ?, ?, ?, ?, ?, ?, 'lecture')
    #             """, (self.get_department_id(selected_depts[0]), level_id, course_id, lecturer_id,
    #                 theory_hours, practical_hours, practical_groups_count))

    #             for dept_name in selected_depts:
    #                 dept_id = self.get_department_id(dept_name)
                    
    #                 cursor.execute("""
    #                     SELECT 1 FROM Course_Department 
    #                     WHERE Course_ID = ? AND Department_ID = ?
    #                 """, (course_id, dept_id))
                    
    #                 if not cursor.fetchone():
    #                     cursor.execute("""
    #                         INSERT INTO Course_Department (Course_ID, Department_ID) 
    #                         VALUES (?, ?)
    #                     """, (course_id, dept_id))

    #             if practical_hours > 0:
    #                 for dept_name, instructors in practical_instructors.items():
    #                     dept_id = self.get_department_id(dept_name)
    #                     for group_num, instructor_name in enumerate(instructors, 1):
    #                         cursor.execute("""
    #                             INSERT INTO Groups (
    #                                 Department_ID, Levels_ID, Course_ID, Lecturer_ID,
    #                                 Theory_Hours, Practical_Hours, Group_Number, Group_Type
    #                             ) VALUES (?, ?, ?, ?, 0, ?, ?, 'practical')
    #                         """, (dept_id, level_id, course_id, 
    #                             self.get_lecturer_id(instructor_name),
    #                             practical_hours, group_num))

    #             conn.commit()

    #             self.update_ui_after_add(
    #                 selected_depts, year_level, instructor, subject,
    #                 theory_hours, practical_hours, practical_instructors,
    #                 practical_groups_count
    #             )

    #             messagebox.showinfo("نجاح", "تمت إضافة المجموعة وربطها بالأقسام بنجاح")

    #         except pyodbc.Error as e:
    #             conn.rollback()
    #             raise ValueError(f"خطأ في قاعدة البيانات: {str(e)}")
    #         finally:
    #             conn.close()

    #     except ValueError as e:
    #         messagebox.showerror("خطأ", str(e))
    #     except Exception as e:
    #         messagebox.showerror("خطأ غير متوقع", f"حدث خطأ: {str(e)}")

    def add_group(self):
        """إضافة مجموعة جديدة مع الربط الصحيح بين المادة والأقسام"""
        try:
            selected_depts = [cb.get() for cb in self.dept_comboboxes if cb.get()]
            if not selected_depts:
                raise ValueError("يجب اختيار قسم واحد على الأقل")

            year_level = self.year_combobox.get()
            instructor = self.instructor_entry.get().strip()
            subject = self.subject_entry.get().strip()
            theory_hours = int(self.theory_hours.get())
            practical_hours = int(self.practical_hours.get())

            if not all([year_level, instructor, subject]):
                raise ValueError("جميع الحقول المميزة بعلامة (*) مطلوبة")

            self.validate_group_uniqueness(selected_depts, year_level, subject, theory_hours, practical_hours)

            # احصل على عدد المجموعات لكل قسم من الواجهة الجديدة
            dept_groups_count = {}
            if practical_hours > 0:
                for dept, spinbox in self.dept_groups_count_spinboxes.items():
                    try:
                        groups_count = int(spinbox.get())
                        dept_groups_count[dept] = groups_count
                    except ValueError:
                        raise ValueError(f"عدد المجموعات غير صالح للقسم {dept}")

            practical_instructors = self.get_practical_instructors() if practical_hours > 0 else {}

            conn = self.connect_db()
            if not conn:
                raise ValueError("فشل الاتصال بقاعدة البيانات")

            cursor = conn.cursor()

            try:
                # الحصول على معرفات المواد والمحاضرين والمستويات
                cursor.execute("SELECT Course_ID FROM Courses WHERE Course_name=?", (subject,))
                course_id = cursor.fetchone()[0]

                cursor.execute("SELECT Lecturer_ID FROM Lecturer WHERE F_name + ' ' + L_name=?", (instructor,))
                lecturer_id = cursor.fetchone()[0]

                cursor.execute("SELECT Levels_ID FROM Levels WHERE Levels_name=?", (year_level,))
                level_id = cursor.fetchone()[0]

                # إضافة المجموعة النظرية (لا يوجد عدد مجموعات في هذه النسخة)
                cursor.execute("""
                    INSERT INTO Groups (
                        Department_ID, Levels_ID, Course_ID, Lecturer_ID,
                        Theory_Hours, Practical_Hours, Group_Type
                    ) VALUES (?, ?, ?, ?, ?, ?, 'lecture')
                """, (self.get_department_id(selected_depts[0]), level_id, course_id, lecturer_id,
                    theory_hours, practical_hours))

                # ربط المادة بالأقسام المختارة
                for dept_name in selected_depts:
                    dept_id = self.get_department_id(dept_name)
                    
                    # التحقق من وجود الربط مسبقاً
                    cursor.execute("""
                        SELECT 1 FROM Course_Department 
                        WHERE Course_ID = ? AND Department_ID = ?
                    """, (course_id, dept_id))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO Course_Department (Course_ID, Department_ID) 
                            VALUES (?, ?)
                        """, (course_id, dept_id))

                # إضافة المجموعات العملية لكل قسم
                if practical_hours > 0:
                    for dept_name, instructors in practical_instructors.items():
                        dept_id = self.get_department_id(dept_name)
                        groups_count = dept_groups_count.get(dept_name, 1)
                        
                        # التأكد من تطابق عدد المحاضرين مع عدد المجموعات
                        if len(instructors) != groups_count:
                            raise ValueError(f"عدد المحاضرين لا يتطابق مع عدد المجموعات للقسم {dept_name}")
                        
                        for group_num, instructor_name in enumerate(instructors, 1):
                            cursor.execute("""
                                INSERT INTO Groups (
                                    Department_ID, Levels_ID, Course_ID, Lecturer_ID,
                                    Theory_Hours, Practical_Hours, Group_Number, Group_Type
                                ) VALUES (?, ?, ?, ?, 0, ?, ?, 'practical')
                            """, (dept_id, level_id, course_id, 
                                self.get_lecturer_id(instructor_name),
                                practical_hours, group_num))

                conn.commit()

                # تحديث واجهة المستخدم بعد الإضافة
                self.update_ui_after_add(
                    selected_depts, year_level, instructor, subject,
                    theory_hours, practical_hours, practical_instructors,
                    dept_groups_count
                )

                messagebox.showinfo("نجاح", "تمت إضافة المجموعة وربطها بالأقسام بنجاح")

            except pyodbc.Error as e:
                conn.rollback()
                raise ValueError(f"خطأ في قاعدة البيانات: {str(e)}")
            finally:
                conn.close()

        except ValueError as e:
            messagebox.showerror("خطأ", str(e))
        except Exception as e:
            messagebox.showerror("خطأ غير متوقع", f"حدث خطأ: {str(e)}")

    # def get_department_id(self, dept_name):
    #     conn = self.connect_db()
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT Department_ID FROM Department WHERE Department_name=?", (dept_name,))
    #         result = cursor.fetchone()
    #         if result:
    #             return result[0]
    #         else:
    #             raise ValueError(f"القسم {dept_name} غير موجود في قاعدة البيانات")
    #     finally:
    #         conn.close()

    def get_department_id(self, department_name):
        try:
            db = Database()
            query = "SELECT Department_ID FROM Department WHERE Department_name = ?"
            db.cursor.execute(query, (department_name,))
            result = db.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ في جلب معرف القسم: {str(e)}")
            return None
        finally:
            db.connection.close()

    def get_lecturer_id(self, lecturer_name):
        conn = self.connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Lecturer_ID FROM Lecturer WHERE F_name + ' ' + L_name=?", (lecturer_name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                raise ValueError(f"المحاضر {lecturer_name} غير موجود في قاعدة البيانات")
        finally:
            conn.close()

    def validate_group_uniqueness(self, selected_depts, year_level, subject, theory_hours, practical_hours):
        conn = self.connect_db()
        cursor = conn.cursor()
        
        for dept in selected_depts:
            cursor.execute("""
                SELECT 1 FROM Groups g
                JOIN Department d ON g.Department_ID = d.Department_ID
                JOIN Levels l ON g.Levels_ID = l.Levels_ID
                JOIN Courses c ON g.Course_ID = c.Course_ID
                WHERE l.Levels_name = ?
                AND c.Course_name = ?
                AND d.Department_name = ?
                AND g.Group_Type = 'lecture'
            """, (year_level, subject, dept))
            
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"المادة {subject} مضافه بالفعل للقسم {dept} والمستوى {year_level}")
        
        conn.close()

    def update_groups_list(self, new_groups):
        """طريقة مركزية لتحديث قائمة المجموعات"""
        self.groups = new_groups
        self.refresh_group_list()
        self.data_manager.groups_data = self.groups

    def update_ui_after_add(self, departments, year_level, instructor, subject,
                        theory_hours, practical_hours, practical_instructors,
                        practical_groups_count):
        lecture_group = {
            'departments': departments,
            'year_level': year_level,
            'instructor': instructor,
            'subject': subject,
            'theory_hours': theory_hours,
            'practical_hours': practical_hours,
            'practical_instructors': practical_instructors,
            'Group_Type': 'lecture',
            'duration': theory_hours,
            'practical_groups_count': practical_groups_count
        }
        
        self.groups.append(lecture_group)
        
        if practical_hours > 0:
            for dept, instructors in practical_instructors.items():
                for group_num, instructor in enumerate(instructors, start=1):
                    practical_group = {
                        'departments': [dept],
                        'year_level': year_level,
                        'instructor': instructor,
                        'subject': subject,
                        'theory_hours': 0,
                        'practical_hours': practical_hours,
                        'practical_instructors': {},
                        'Group_Type': 'practical',
                        'duration': practical_hours,
                        'group_number': group_num
                    }
                    self.groups.append(practical_group)

        self.refresh_group_list()
        self.clear_input_fields()

    # display the grous --> practical or theory
    def format_group_display(self, group):
        depts = "، ".join(group['departments'])
        
        if group['Group_Type'] == 'practical':
            group_num = f" (المجموعة {group.get('group_number', 1)})" if 'group_number' in group else ""
            return f"{depts} | {group['year_level']} | {group['subject']} | عملي{group_num} | {group['instructor']} | {group['practical_hours']}ساعة"
        else:
            return f"{depts} | {group['year_level']} | {group['subject']} | {group['instructor']} | {group['theory_hours']}ساعة"
        
    def validate_departments(self, selected_depts):
        """التحقق من عدم تكرار الأقسام"""
        if len(selected_depts) != len(set(selected_depts)):
            raise ValueError("لا يمكن اختيار نفس القسم أكثر من مرة")
        if not selected_depts:
            raise ValueError("يجب اختيار قسم واحد على الأقل")
        return True

    def check_duplicate_departments(self, event=None):
        try:
            selected_depts = []
            for cb in self.dept_comboboxes:
                dept = cb.get()
                if dept:
                    selected_depts.append(dept)
            
            if len(selected_depts) != len(set(selected_depts)):
                messagebox.showerror("خطأ", "لا يمكن اختيار نفس القسم أكثر من مرة")
                # Reset the last changed combobox
                if event:
                    event.widget.set('')
        except Exception:
            pass  
    
    def clear_input_fields(self):
        # Clear department selection (keep at least one row)
        for widget in self.dept_container.winfo_children():
            widget.destroy()
        self.dept_comboboxes = []
        self.add_dept_row()
        
        # Clear other fields
        self.year_combobox.set('')
        self.subject_entry.set('')
        self.instructor_entry.set('')
        self.theory_hours.set(1)
        self.practical_hours.set(0)
        # self.practical_groups_count.set(1)
        self.toggle_practical_fields()
        self.group_search_entry.delete(0, tk.END)

    def filter_group_list(self, event=None):
        search_term = self.group_search_entry.get().lower()
        self.group_listbox.delete(0, tk.END)
        
        for group in self.groups:
            display_text = self.format_group_display(group)
            if search_term in display_text.lower():
                self.group_listbox.insert(tk.END, display_text)

    def refresh_group_list(self):
        self.group_listbox.delete(0, tk.END)
        for group in sorted(self.groups, key=lambda g: (g['departments'][0], g['year_level'], g['instructor'])):
            self.group_listbox.insert(tk.END, self.format_group_display(group))

    # add more than one department ---> row
    def add_dept_row(self):
        row_frame = tk.Frame(self.dept_container,bg="white")
        row_frame.pack(fill=tk.X, pady=2, anchor='e')
        
        # Add "القسم" label before the combobox
        tk.Label(row_frame, text=": القسم",font=('Arial Unicode MS', 11,'bold'),bg="white").pack(side=tk.RIGHT, padx=5)
        
        dept_combobox = ttk.Combobox(row_frame, values=self.departments, state="readonly",width=32,style="Custom.TCombobox")
        dept_combobox.pack(side=tk.RIGHT, padx=5)
        dept_combobox.bind("<<ComboboxSelected>>", self.check_duplicate_departments)
        self.dept_comboboxes.append(dept_combobox)
        
        # Only show delete button for additional rows (not the first one)
        if len(self.dept_comboboxes) > 1:
            remove_btn = ttk.Button(row_frame, text="حذف", 
                                 command=lambda: self.remove_depart_row(row_frame, dept_combobox))
            remove_btn.pack(side=tk.RIGHT, padx=5)

    def remove_depart_row(self, row_frame, combobox):
        """Remove a department row"""
        if len(self.dept_comboboxes) > 1:
            row_frame.destroy()
            self.dept_comboboxes.remove(combobox)
            # Update practical instructors UI if needed
            if int(self.practical_hours.get()) > 0:
                self.toggle_practical_fields()

    def load_groups_from_db(self):
        """تحميل المجموعات من قاعدة البيانات مع الأقسام الإضافية"""
        conn = self.connect_db()
        if not conn:
            messagebox.showerror("خطأ", "فشل الاتصال بقاعدة البيانات")
            return
            
        try:
            cursor = conn.cursor()
            self.groups = [] 
            
            cursor.execute("""
                SELECT 
                    g.Group_ID, 
                    c.Course_name, 
                    l.Levels_name, 
                    d.Department_name,
                    lec.F_name + ' ' + lec.L_name AS Lecturer_Name,
                    g.Theory_Hours, 
                    g.Practical_Hours, 
                    g.Group_Number,
                    g.Group_Type,
                    g.Practical_Groups_Count
                FROM Groups g
                JOIN Courses c ON g.Course_ID = c.Course_ID
                JOIN Levels l ON g.Levels_ID = l.Levels_ID
                JOIN Lecturer lec ON g.Lecturer_ID = lec.Lecturer_ID
                JOIN Department d ON g.Department_ID = d.Department_ID
                ORDER BY g.Group_Type, c.Course_name, l.Levels_name
            """)
            
            all_groups = cursor.fetchall()
            
            for group in all_groups:
                if group[8] == 'lecture':
                    cursor.execute("""
                        SELECT d.Department_name 
                        FROM Course_Department cd
                        JOIN Department d ON cd.Department_ID = d.Department_ID
                        WHERE cd.Course_ID = (
                            SELECT Course_ID FROM Courses WHERE Course_name = ?
                        )
                    """, (group[1],))
                    departments = [row[0] for row in cursor.fetchall()]
                else:
                    departments = [group[3]]
                
                group_data = {
                    'departments': departments,
                    'year_level': group[2],
                    'instructor': group[4],
                    'subject': group[1],
                    'theory_hours': group[5],
                    'practical_hours': group[6],
                    'Group_Type': group[8],
                    'duration': group[5] if group[8] == 'lecture' else group[6],
                    'group_number': group[7] if group[8] == 'practical' else None,
                    'practical_groups_count': group[9] if group[8] == 'lecture' else None,
                    'practical_instructors': {}
                }
                
                if group[8] == 'lecture':
                    cursor.execute("""
                        SELECT d.Department_name, lec.F_name + ' ' + lec.L_name AS Instructor_Name
                        FROM Groups g
                        JOIN Lecturer lec ON g.Lecturer_ID = lec.Lecturer_ID
                        JOIN Department d ON g.Department_ID = d.Department_ID
                        WHERE g.Course_ID = (SELECT Course_ID FROM Courses WHERE Course_name=?)
                        AND g.Levels_ID = (SELECT Levels_ID FROM Levels WHERE Levels_name=?)
                        AND g.Group_Type = 'practical'
                        ORDER BY g.Group_Number
                    """, (group[1], group[2]))
                    
                    practical_instructors = {}
                    for row in cursor.fetchall():
                        dept = row[0]
                        instructor = row[1]
                        if dept not in practical_instructors:
                            practical_instructors[dept] = []
                        practical_instructors[dept].append(instructor)
                    
                    group_data['practical_instructors'] = practical_instructors
                    
                    self.groups.append(group_data)
                else:
                    self.groups.append(group_data)
            
            self.refresh_group_list()
            self.data_manager.groups_data = self.groups
            
        except pyodbc.Error as e:
            messagebox.showerror("خطأ في قاعدة البيانات", f"فشل تحميل المجموعات: {str(e)}")
        finally:
            conn.close()

    def check_group_in_schedules(self, group):
        """التحقق مما إذا كانت المجموعة موجودة في أي جدول"""
        conn = self.connect_db()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT d.Department_name, lv.Levels_name
                FROM schedule s
                JOIN groups g ON s.group_id = g.group_id
                JOIN department d ON g.Department_ID = d.Department_ID
                JOIN levels lv ON g.Levels_ID = lv.Levels_ID
                JOIN courses c ON g.Course_ID = c.Course_ID
                JOIN lecturer lec ON g.Lecturer_ID = lec.Lecturer_ID
                WHERE c.Course_name = ?
                AND lv.Levels_name = ?
                AND lec.F_name + ' ' + lec.L_name = ?
                AND g.Group_Type = ?
                AND (g.Group_Number = ? OR ? IS NULL)
            """, (
                group['subject'],
                group['year_level'],
                group['instructor'],
                group['Group_Type'],
                group.get('group_number'),
                1 if group['Group_Type'] == 'lecture' else None
            ))
            
            return cursor.fetchall()
            
        except pyodbc.Error as e:
            messagebox.showerror("خطأ في قاعدة البيانات", f"فشل التحقق من الجداول: {str(e)}")
            return []
        finally:
            conn.close()

    def delete_group(self):
        """حذف مجموعة مع حذف جميع علاقاتها في Course_Department"""
        selected = self.group_listbox.curselection()
        if not selected:
            messagebox.showerror("خطأ", "الرجاء تحديد مجموعة للحذف!")
            return

        index = selected[0]
        if index >= len(self.groups):
            return

        group_to_delete = self.groups[index]

        # تأكيد الحذف
        confirm_msg = f"هل أنت متأكد من حذف المجموعة التالية؟\n\n"
        confirm_msg += f"المادة: {group_to_delete['subject']}\n"
        confirm_msg += f"المستوى: {group_to_delete['year_level']}\n"
        confirm_msg += f"الأقسام: {', '.join(group_to_delete['departments'])}"
        
        if not messagebox.askyesno("تأكيد الحذف", confirm_msg):
            return

        conn = None
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            cursor.execute("SELECT Course_ID FROM Courses WHERE Course_name=?", (group_to_delete['subject'],))
            course_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT Levels_ID FROM Levels WHERE Levels_name=?", (group_to_delete['year_level'],))
            level_id = cursor.fetchone()[0]

            cursor.execute("""
                DELETE FROM Course_Department 
                WHERE Course_ID = ?
            """, (course_id,))

            cursor.execute("""
                DELETE FROM Schedule
                WHERE Group_ID IN (
                    SELECT Group_ID FROM Groups
                    WHERE Course_ID = ? AND Levels_ID = ?
                )
            """, (course_id, level_id))

            cursor.execute("""
                DELETE FROM Groups 
                WHERE Course_ID = ? AND Levels_ID = ?
                AND Group_Type = 'practical'
            """, (course_id, level_id))

            cursor.execute("""
                DELETE FROM Groups 
                WHERE Course_ID = ? AND Levels_ID = ?
                AND Group_Type = 'lecture'
            """, (course_id, level_id))

            conn.commit()

            self.groups = [g for g in self.groups if not (
                g['subject'] == group_to_delete['subject'] and 
                g['year_level'] == group_to_delete['year_level']
            )]
            
            self.refresh_group_list()
            messagebox.showinfo("نجاح", "تم الحذف بنجاح مع جميع العلاقات المرتبطة")

        except pyodbc.Error as e:
            if conn:
                conn.rollback()
            messagebox.showerror("خطأ", f"فشل الحذف: {str(e)}")
        finally:
            if conn:
                conn.close()

    def delete_appointment_and_group(self, day, start_time):
        """حذف موعد من الجدول وقاعدة البيانات وإزالة المجموعة من الـ groups"""
        if not self.current_schedule_key:
            return

        conn = self.connect_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # الحصول على بيانات الموعد المراد حذفه
            appointments = self.schedule_data[self.current_schedule_key]['schedule'].get(day, [])
            target_appt = next((a for a in appointments if a['start'] == start_time), None)

            if not target_appt:
                return

            group_to_delete = target_appt['group']

            # 1. حذف الموعد من جدول schedule
            query = """
                DELETE FROM schedule
                WHERE group_id IN (
                    SELECT g.group_id
                    FROM groups g
                    JOIN department d ON g.Department_ID = d.Department_ID
                    JOIN levels lv ON g.Levels_ID = lv.Levels_ID
                    JOIN courses c ON g.Course_ID = c.Course_ID
                    JOIN lecturer lec ON g.Lecturer_ID = lec.Lecturer_ID
                    WHERE d.Department_name = ?
                    AND lv.Levels_name = ?
                    AND c.Course_name = ?
                    AND lec.F_name + ' ' + lec.L_name = ?
                    AND g.Group_Type = ?
            """
            params = [
                self.schedule_data[self.current_schedule_key]['dept'],
                self.schedule_data[self.current_schedule_key]['year'],
                group_to_delete['subject'],
                group_to_delete['instructor'],
                group_to_delete['Group_Type']
            ]

            if group_to_delete['Group_Type'] == 'practical':
                query += " AND g.Group_Number = ?"
                params.append(group_to_delete.get('group_number', 1))

            query += ")"
            cursor.execute(query, params)

            if group_to_delete['Group_Type'] == 'lecture':
                for dept in group_to_delete['departments']:
                    delete_practical_query = """
                        DELETE FROM groups
                        WHERE Course_ID = (SELECT Course_ID FROM courses WHERE Course_name = ?)
                        AND Department_ID = (SELECT Department_ID FROM department WHERE Department_name = ?)
                        AND Levels_ID = (SELECT Levels_ID FROM levels WHERE Levels_name = ?)
                        AND Group_Type = 'practical'
                    """
                    cursor.execute(delete_practical_query, [
                        group_to_delete['subject'],
                        dept,
                        group_to_delete['year_level']
                    ])

            delete_group_query = """
                DELETE FROM groups
                WHERE Course_ID = (SELECT Course_ID FROM courses WHERE Course_name = ?)
                AND Lecturer_ID = (SELECT Lecturer_ID FROM lecturer WHERE F_name + ' ' + L_name = ?)
                AND Levels_ID = (SELECT Levels_ID FROM levels WHERE Levels_name = ?)
                AND Group_Type = ?
            """
            params = [
                group_to_delete['subject'],
                group_to_delete['instructor'],
                group_to_delete['year_level'],
                group_to_delete['Group_Type']
            ]

            if group_to_delete['Group_Type'] == 'practical':
                delete_group_query += " AND Group_Number = ?"
                params.append(group_to_delete.get('group_number', 1))

            cursor.execute(delete_group_query, params)

            conn.commit()

            groups_to_remove = [g for g in self.groups_data
                                if g['subject'] == group_to_delete['subject'] and
                                g['year_level'] == group_to_delete['year_level'] and
                                g['instructor'] == group_to_delete['instructor'] and
                                g['Group_Type'] == group_to_delete['Group_Type'] and
                                (g.get('group_number') == group_to_delete.get('group_number', 1) if group_to_delete['Group_Type'] == 'practical' else True)]

            for g in groups_to_remove:
                if g in self.groups_data:
                    self.groups_data.remove(g)

            for schedule_key, schedule_info in self.schedule_data.items():
                for d, appointments in schedule_info['schedule'].items():
                    schedule_info['schedule'][d] = [
                        appt for appt in appointments
                        if not (appt['group']['subject'] == group_to_delete['subject'] and
                                appt['group']['year_level'] == group_to_delete['year_level'] and
                                appt['group']['instructor'] == group_to_delete['instructor'] and
                                appt['group']['Group_Type'] == group_to_delete['Group_Type'] and
                                (appt['group'].get('group_number') == group_to_delete.get('group_number', 1) if group_to_delete['Group_Type'] == 'practical' else True))
                    ]

            self.data_manager.schedule_data = self.schedule_data
            self.create_schedule_table()
            self.filter_groups()
            messagebox.showinfo("نجاح", "تم حذف الموعد والمجموعة بنجاح")

        except pyodbc.Error as e:
            conn.rollback()
            messagebox.showerror("خطأ في قاعدة البيانات", f"فشل حذف الموعد: {str(e)}")
        finally:
            conn.close()
            
# Entering schedules
class SchedulePlacerPage(BasePage):
    def __init__(self, parent, return_callback, groups_data):
        super().__init__(parent, return_callback)
        self.data_manager = DataManager()
        self.groups_data = groups_data
        self.schedule_data = self.data_manager.schedule_data or {} 
        self.selected_group = None
        self.filtered_groups_data = []
        self.current_schedule_key = None
        self.edit_mode = False

        self.SERVER = '.'
        self.DATABASE = 'project'
        self.locations = []

        # تغيير من pack إلى grid للإطار الرئيسي
        self.grid_rowconfigure(0, weight=1)  # الصف العلوي (المحتوى) يتمدد
        self.grid_columnconfigure(0, weight=1)
        
        self.main_content = tk.Frame(self)
        self.main_content.grid(row=0, column=0, sticky="nsew")  # تغيير هنا

        # تعديل زر العودة ليكون في صف منفصل
        back_button = ttk.Button(
            self,  # نضعه مباشرة في النافذة الرئيسية
            text="العودة للرئيسية",
            command=self.return_callback,
            style='Rounded.TButton',
            width= 20
        )
        back_button.grid(row=1, column=0, pady=20)  # تغيير هنا
        
        self.setup_ui()
        self.load_locations_from_db()
        self.load_schedules_from_db()
        self.load_initial_data()
        

    def connect_db(self):
        try:
            # الحصول على إعدادات الاتصال من الصفحة الرئيسية
            main_page = self.master.master if isinstance(self.master, tk.Toplevel) else self.master
            if hasattr(main_page, 'db_server') and hasattr(main_page, 'db_name'):
                self.SERVER = main_page.db_server
                self.DATABASE = main_page.db_name
            
            conn = pyodbc.connect(
                f'DRIVER={{SQL Server}};SERVER={self.SERVER};'
                f'DATABASE={self.DATABASE};Trusted_Connection=yes;'
                )
            return conn
        except pyodbc.Error as e:
            messagebox.showerror("خطأ في الاتصال", f"فشل الاتصال بقاعدة البيانات:\n{str(e)}")
            return None
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")
            return None
        
    def setup_ui(self):
        #Label frame for department and 
        selection_frame = ttk.LabelFrame(self.main_content, text="اختيار القسم والسنة الدراسية", padding=(10, 10), labelanchor="ne")
        selection_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)  # تغيير هنا

        selection_row = tk.Frame(selection_frame)
        selection_row.pack(fill=tk.X, pady=5)  # يمكن تركها pack لأنها داخل إطار آخر

        # select the departmrnt
        tk.Label(selection_row, text=": القسم",font=('Arial', 12, 'bold')).pack(side=tk.RIGHT, padx=5)
        self.dept_combobox = ttk.Combobox(selection_row, 
                                        values=self.get_unique_departments(), 
                                        state="readonly",
                                        width=25)
        self.dept_combobox.pack(side=tk.RIGHT, padx=10)
        self.dept_combobox.bind("<<ComboboxSelected>>", self.on_dept_year_change)

        # select the year
        tk.Label(selection_row, text=": السنة الدراسية").pack(side=tk.RIGHT, padx=5)
        self.year_combobox = ttk.Combobox(selection_row, 
                                        values=self.get_unique_year_levels(), 
                                        state="readonly",
                                        width=25)
        self.year_combobox.pack(side=tk.RIGHT, padx=10)
        self.year_combobox.bind("<<ComboboxSelected>>", self.on_dept_year_change)

        group_frame = ttk.LabelFrame(self.main_content, text="اختيار المجموعة والمكان والوقت", padding=(10, 10), labelanchor="ne")
        group_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)  # تغيير هنا

        group_row = tk.Frame(group_frame)
        group_row.pack(fill=tk.X, pady=5)

        # select group
        tk.Label(group_row, text=": المجموعة").pack(side=tk.RIGHT, padx=5)
        self.group_combobox = ttk.Combobox(group_row, state="readonly", width=35)
        self.group_combobox.pack(side=tk.RIGHT, padx=10)
        self.group_combobox.bind("<<ComboboxSelected>>", self.select_group)

        # select place
        tk.Label(group_row, text=": المكان").pack(side=tk.RIGHT, padx=5)
        self.place_combobox = ttk.Combobox(
            group_row,
            values=self.locations,  # استخدام القائمة المحملة
            state="readonly",
            width=25
        )
        self.place_combobox.pack(side=tk.RIGHT, padx=10)


        # select subject
        tk.Label(group_row, text=": المدة (ساعات)").pack(side=tk.RIGHT, padx=5)
        self.duration_combobox = ttk.Combobox(group_row, 
                                            values=[1, 2, 3], 
                                            state="disabled",  # تعطيل الاختيار يدوياً
                                            width=5)
        self.duration_combobox.pack(side=tk.RIGHT, padx=10)

        # Schedule edit button ---> not working yet
        self.edit_button = ttk.Button(group_frame, text="تعديل الجدول", command=self.toggle_edit_mode)
        self.edit_button.pack(pady=5)

        self.table_container = tk.Frame(self.main_content)
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.main_content.grid_rowconfigure(2, weight=1)  # الجدول يتمدد
        self.main_content.grid_columnconfigure(0, weight=1)
            
        self.create_schedule_table()

    def load_initial_data(self):
        # Check if comboboxes exist
        if not hasattr(self, 'dept_combobox') or not hasattr(self, 'year_combobox'):
            return
            
        conn = self.connect_db()
        try:
            cursor = conn.cursor()
            
            # load departs
            cursor.execute("SELECT Department_name FROM Department")
            departments = [row[0] for row in cursor.fetchall()]
            self.dept_combobox['values'] = departments
            
            # load years
            cursor.execute("SELECT Levels_name FROM Levels")
            year_levels = [row[0] for row in cursor.fetchall()]
            self.year_combobox['values'] = year_levels
            
        except pyodbc.Error as e:
            messagebox.showerror("خطأ", f"تعذر تحميل البيانات الأولية: {str(e)}")
        finally:
            if conn:
                conn.close()

    # not working yet ---> need edit           
    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        self.edit_button.config(text="إنهاء التعديل" if self.edit_mode else "تعديل الجدول")
        self.create_schedule_table()  # Refresh the table to update colors and bindings

    def get_unique_year_levels(self):
            year_levels = set()
            for group in self.groups_data:
                year_levels.add(group['year_level'])
            return sorted(list(year_levels))
    def get_unique_departments(self):
        departments = set()
        for group in self.groups_data:
            for dept in group['departments']:
                departments.add(dept)
        return sorted(list(departments))
    
    def select_group(self, event):
        selected_index = self.group_combobox.current()
        if selected_index >= 0 and hasattr(self, 'filtered_groups_data'):
            self.selected_group = self.filtered_groups_data[selected_index]
            print(f"Selected group: {self.selected_group}")  # للتصحيح
            duration = self.selected_group.get('duration')
            if duration is not None and isinstance(duration, (int, float)) and duration > 0:
                self.duration_combobox.set(str(int(duration)))
            else:
                self.duration_combobox.set('1')
                messagebox.showwarning("تحذير", f"المدة غير محددة أو غير صالحة ({duration}), تم تعيين القيمة الافتراضية 1")
            self.duration_combobox.config(state='disabled')


    def get_all_reserved_places(self):
        """الحصول على جميع الأماكن المحجوزة عبر جميع الجداول مع أوقاتها"""
        reserved_places = {}
        
        for schedule_key, schedule_info in self.schedule_data.items():
            for day, appointments in schedule_info['schedule'].items():
                for appt in appointments:
                    place = appt['place']
                    day_time = (day, appt['start'], appt['end'])
                    
                    if place not in reserved_places:
                        reserved_places[place] = []
                    reserved_places[place].append(day_time)
        
        return reserved_places
    
    def update_group_combobox(self):
        """تحديث قائمة المجموعات مع التنسيق المناسب"""
        display_list = []
        for group in self.filtered_groups_data:
            text = f"{group['subject']} - {group['instructor']}"
            if group['Group_Type'] == 'practical':
                text += f" (المجموعة {group['group_number']})"
            display_list.append(text)
        self.group_combobox['values'] = display_list
        
    def is_place_reserved(self, place, day, start, end, current_group=None):
        """التحقق من تعارض المكان مع تحسينات الأداء والمنطق"""
        if not place or not day or not start or not end:
            return False

        # check conflicts ---> local data
        for schedule_key, schedule_info in self.schedule_data.items():
            # theory for more than one depart check
            if (current_group and current_group['Group_Type'] == 'lecture' and 
                len(current_group['departments']) > 1 and
                schedule_key != self.current_schedule_key):
                continue
                
            for existing_day, appointments in schedule_info.get('schedule', {}).items():
                if existing_day != day:
                    continue
                    
                for appt in appointments:
                    if appt['place'] == place and not (end <= appt['start'] or start >= appt['end']):
                        # except the participated theory lectures
                        if (current_group and current_group['Group_Type'] == 'lecture' and
                            appt['group']['Group_Type'] == 'lecture' and
                            appt['group']['subject'] == current_group['subject'] and
                            appt['group']['instructor'] == current_group['instructor']):
                            return False
                        return True

        # db check conflicts
        conn = None
        cursor = None
        try:
            conn = self.connect_db()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            query = """
                SELECT COUNT(*) 
                FROM schedule sch
                JOIN location loc ON sch.location_id = loc.location_id
                WHERE loc.Location_name = ?
                AND sch.day = ?
                AND NOT (sch.end_time <= ? OR sch.start_time >= ?)
            """
            
            # if the lecture was participated --- > skip conflict error
            if current_group and current_group['Group_Type'] == 'lecture':
                query += """
                    AND NOT EXISTS (
                        SELECT 1 FROM groups g
                        JOIN courses c ON g.Course_ID = c.Course_ID
                        JOIN lecturer lec ON g.Lecturer_ID = lec.Lecturer_ID
                        WHERE g.group_id = sch.group_id
                        AND c.Course_name = ?
                        AND lec.F_name + ' ' + lec.L_name = ?
                        AND g.Group_Type = 'lecture'
                    )
                """
                cursor.execute(query, (place, day, start, end, 
                                    current_group['subject'], current_group['instructor']))
            else:
                cursor.execute(query, (place, day, start, end))
                
            conflict_count = cursor.fetchone()[0]
            return conflict_count > 0
            
        except pyodbc.Error as e:
            messagebox.showerror("خطأ", f"تعذر التحقق من التعارضات في قاعدة البيانات: {str(e)}")
            return True 
        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except Exception:
                pass


    def create_schedule_table(self):
        """Create/update the schedule table with conflict highlighting"""
        # Clear old table if exists
        for widget in self.table_container.winfo_children():
            widget.destroy()

        if not self.current_schedule_key:
            return

        self.times = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        self.days = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
        total_columns = len(self.times) - 1

        # Table frame
        self.table_frame = tk.Frame(self.table_container, bg="#edede9")
        self.table_frame.pack(fill="both", expand=True)

        # Column header (Day/Time)
        header_label = tk.Label(
            self.table_frame,
            text="اليوم / الوقت",
            bg="light gray",
            relief="solid",
            width=15,
            height=2,
            anchor='center',
            font=('Arial', 10, 'bold')
        )
        header_label.grid(row=0, column=total_columns, sticky="nsew")

        for idx, time in enumerate(self.times[:-1]):
            col = 10 - idx
            tk.Label(self.table_frame, text=f"{time+1}:00 - {time}:00", 
                    bg='#d3d3d3', relief="groove").grid(row=0, column=col, sticky="nsew")

        # Days + empty cells
        for row_idx, day in enumerate(self.days, 1):
            # Day label
            day_label = tk.Label(
                self.table_frame,
                text=day,
                bg="light gray",
                relief="groove",
                width=15,
                height=3,
                anchor='center',
                font=('Arial', 10, 'bold')
            )
            day_label.grid(row=row_idx, column=total_columns, sticky="nsew")

            # Empty cells for each time slot
            for col in range(total_columns):
                start_time = self.times[col]
                end_time = self.times[col + 1]

                # Get current place selection
                current_place = self.place_combobox.get()

                # Only show conflict if there's a place selected and it's reserved
                place_conflict = False
                if current_place:
                    place_conflict = self.is_place_reserved(current_place, day, start_time, end_time)

                cell_bg = "#ffcccc" if place_conflict else "white"

                cell = tk.Label(
                    self.table_frame,
                    bg=cell_bg,
                    relief="solid",
                    width=15,
                    height=3
                )
                cell.grid(row=row_idx, column=col, sticky="nsew")
                if not self.edit_mode:
                    cell.bind("<Button-1>", lambda e, r=row_idx, c=col: self.place_group(r, c))

        # Configure grid weights for resizing
        for col in range(total_columns + 1):
            self.table_frame.grid_columnconfigure(col, weight=1)
        for row in range(len(self.days)+1):
            self.table_frame.grid_rowconfigure(row, weight=1)

        # Load saved schedule for current dept/year
        self.load_saved_schedule()

        # Bind place combobox change to refresh the table
        self.place_combobox.bind("<<ComboboxSelected>>", lambda e: self.refresh_table_conflicts())

    def refresh_table_conflicts(self):
        """Refresh the conflict highlighting when place selection changes"""
        current_place = self.place_combobox.get()
        
        for row_idx, day in enumerate(self.days, 1):
            for col in range(len(self.times)-1):
                start_time = self.times[col]
                end_time = self.times[col + 1]
                
                # Check if current place is reserved at this time
                place_conflict = False
                if current_place:
                    place_conflict = self.is_place_reserved(current_place, day, start_time, end_time)
                
                # Update cell color
                for widget in self.table_frame.grid_slaves(row=row_idx, column=col):
                    if widget.cget('bg') not in ['#d4edda', '#d4e6f1']:  # Don't change occupied cells
                        widget.config(bg="#ffcccc" if place_conflict else "white")

    def filter_groups(self):
        selected_dept = self.dept_combobox.get()
        selected_year = self.year_combobox.get()

        if not selected_dept or not selected_year:
            return

        conn = self.connect_db()
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT Department_ID FROM Department WHERE Department_name = ?", (selected_dept,))
            dept_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT Levels_ID FROM Levels WHERE Levels_name = ?", (selected_year,))
            level_id = cursor.fetchone()[0]
            
            query = """
                SELECT 
                    g.Group_ID,
                    c.Course_name,
                    lec.F_name + ' ' + lec.L_name AS lecturer_name,
                    g.Group_Type,
                    g.Group_Number,
                    d.Department_name,
                    lv.Levels_name,
                    g.Department_ID,
                    g.Levels_ID,
                    g.Theory_Hours,
                    g.Practical_Hours,
                    c.Course_ID,
                    g.Lecturer_ID
                FROM Groups g
                JOIN Courses c ON g.Course_ID = c.Course_ID
                JOIN Lecturer lec ON g.Lecturer_ID = lec.Lecturer_ID
                JOIN Department d ON g.Department_ID = d.Department_ID
                JOIN Levels lv ON g.Levels_ID = lv.Levels_ID
                WHERE d.Department_name = ? 
                AND lv.Levels_name = ?
                AND g.Levels_ID = ?
                AND NOT EXISTS (
                    SELECT 1 FROM Schedule s 
                    WHERE s.Group_ID = g.Group_ID
                    AND s.Department_ID = ?
                )
            """
            cursor.execute(query, (selected_dept, selected_year, level_id, dept_id))
            groups = cursor.fetchall()
            
            self.filtered_groups_data = []
            for group in groups:
                group_data = {
                    'group_id': group[0],
                    'subject': group[1],
                    'instructor': group[2],
                    'Group_Type': group[3],
                    'group_number': group[4],
                    'departments': [group[5]],
                    'year_level': group[6],
                    'dept_id': group[7],
                    'level_id': group[8],
                    'theory_hours': int(group[9]) if group[9] else 1,
                    'practical_hours': int(group[10]) if group[10] else 1,
                    'course_id': group[11],
                    'lecturer_id': group[12],
                    'is_shared': False
                }
                
                if group[3] == 'lecture':
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM Course_Department 
                        WHERE Course_ID = ?
                    """, (group[11],))
                    if cursor.fetchone()[0] > 1:
                        group_data['is_shared'] = True
                        cursor.execute("""
                            SELECT d.Department_name 
                            FROM Course_Department cd
                            JOIN Department d ON cd.Department_ID = d.Department_ID
                            WHERE cd.Course_ID = ?
                        """, (group[11],))
                        group_data['departments'] = [row[0] for row in cursor.fetchall()]
                
                self.filtered_groups_data.append(group_data)
            
            self.update_group_combobox()
            
        except pyodbc.Error as e:
            messagebox.showerror("خطأ", f"تعذر تحميل المجموعات: {str(e)}")
        finally:
            if conn:
                conn.close()

    def on_dept_year_change(self, event=None):
        """عند تغيير القسم أو السنة الدراسية"""
        selected_dept = self.dept_combobox.get()
        selected_year = self.year_combobox.get()

        if not selected_dept or not selected_year:
            return

        new_schedule_key = f"{selected_dept}_{selected_year}"
        
        if new_schedule_key not in self.schedule_data:
            self.schedule_data[new_schedule_key] = {
                'dept': selected_dept,
                'year': selected_year,
                'schedule': {}  # سجل المواعيد
            }
        
        self.current_schedule_key = new_schedule_key
        
        self.filter_groups()
        
        self.create_schedule_table()

    def handle_practical_groups(self, group):
        """إدارة المجموعات العملية حسب القواعد المحددة"""
        conn = self.connect_db()
        try:
            cursor = conn.cursor()
            
            # check practicals num
            query = """
                SELECT COUNT(*) 
                FROM Groups
                WHERE Course_ID = ?
                AND Department_ID = ?
                AND Group_Type = 'practical'
            """
            cursor.execute(query, (group['course_id'], group['dept_id']))
            practical_count = cursor.fetchone()[0]
            
            if practical_count > 1:
                # same time ---> different places
                self.allow_concurrent_practicals = True
            else:
                self.allow_concurrent_practicals = False
                
        except pyodbc.Error as e:
            messagebox.showerror("خطأ", f"تعذر التحقق من المجموعات العملية: {str(e)}")
        finally:
            if conn:
                conn.close()


    def select_group(self, event):
        selected_index = self.group_combobox.current()
        if selected_index >= 0 and hasattr(self, 'filtered_groups_data'):
            self.selected_group = self.filtered_groups_data[selected_index]
            print(f"المجموعة المحددة: {self.selected_group}")  # لأغراض التصحيح
            
            try:
                if self.selected_group['Group_Type'] == 'lecture':
                    duration = self.selected_group['theory_hours']
                else:
                    duration = self.selected_group['practical_hours']
                
                self.duration_combobox.config(state='normal')
                self.duration_combobox.set(str(duration))
                self.duration_combobox.config(state='disabled')
                
                print(f"تم تعيين المدة إلى: {duration} ساعة/ساعات")
                
            except KeyError as e:
                print(f"خطأ في المفاتيح: {e}")
                self.duration_combobox.set('1')
                messagebox.showwarning("تحذير", "بيانات الساعات غير متوفرة، تم تعيين القيمة الافتراضية 1")
            except Exception as e:
                print(f"خطأ غير متوقع: {e}")
                self.duration_combobox.set('1')
                messagebox.showwarning("تحذير", "حدث خطأ، تم تعيين القيمة الافتراضية 1")
            
            # إذا كانت المجموعة عملية، قم بمعالجة المجموعات العملية
            if self.selected_group['Group_Type'] == 'practical':
                self.handle_practical_groups(self.selected_group)

    def is_group_already_scheduled(self, group_id, dept_id):
        """Check if this group is already scheduled in the current week for this department"""
        if not self.current_schedule_key:
            return False
            
        schedule_info = self.schedule_data.get(self.current_schedule_key, {})
        for day, appointments in schedule_info.get('schedule', {}).items():
            for appt in appointments:
                if (appt['group'].get('group_id') == group_id and 
                    appt['group'].get('dept_id') == dept_id):
                    return True
        return False

    def place_group(self, row, col):
        if not self.selected_group:
            messagebox.showwarning("تحذير", "يرجى اختيار مجموعة أولاً")
            return

        current_dept = self.dept_combobox.get()
        current_year = self.year_combobox.get()
        
        if (current_dept not in self.selected_group['departments'] or 
            current_year != self.selected_group['year_level']):
            messagebox.showerror(
                "خطأ", 
                f"هذه المجموعة تنتمي إلى {self.selected_group['year_level']} - {', '.join(self.selected_group['departments'])}\n"
                f"ولا تنتمي إلى {current_year} - {current_dept}"
            )
            return

        try:
            duration = int(self.duration_combobox.get())
            start_col = col - duration + 1
            day = self.days[row-1]
            start_time = self.times[start_col]
            end_time = self.times[col + 1]
            place = self.place_combobox.get()

            if self.is_group_already_scheduled(self.selected_group['group_id'], self.selected_group['dept_id']):
                messagebox.showwarning("تحذير", "هذه المجموعة مضافوة بالفعل في الجدول!")
                return

            save_success = self.save_schedule(day, start_time, end_time, place, self.selected_group)
            
            if save_success:
                # delete group from list
                self.remove_group_from_filtered_data(self.selected_group['group_id'])
                self.group_combobox.set('')

                self.refresh_schedule_table()
        except ValueError:
            messagebox.showerror("خطأ", "بيانات غير صالحة")
            
    def remove_group_from_filtered_data(self, group_id):
        if not group_id:
            return
            
        self.filtered_groups_data = [
            g for g in self.filtered_groups_data 
            if g.get('group_id') != group_id
        ]
        self.update_group_combobox()

    def refresh_schedule_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        self.create_schedule_table()
        self.load_saved_schedule()

    def remove_group_from_all_lists(self, group_id):
        """إزالة المجموعة من القوائم مع التحقق من وجودها"""
        if not group_id:
            return
            
        self.filtered_groups_data = [
            g for g in self.filtered_groups_data 
            if g.get('group_id') != group_id
        ]
        
        self.groups_data = [
            g for g in self.groups_data 
            if g.get('group_id') != group_id
        ]
        
        self.update_group_combobox()

    def remove_from_other_lists(self, dept, year):
        for group in self.filtered_groups_data[:]:
            if (group['subject'] == self.selected_group['subject'] and 
                group['Group_Type'] == 'lecture' and 
                dept in group['departments']):
                self.filtered_groups_data.remove(group)
        self.update_group_combobox()
        
    def load_locations_from_db(self):
        conn = None
        cursor = None
        try:
            conn = self.connect_db()
            if not conn:
                return []

            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'Location'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                messagebox.showerror("خطأ", "جدول الأماكن غير موجود في قاعدة البيانات")
                return []

            cursor.execute("""
                SELECT 
                    Location_ID,
                    Location_name,
                    ISNULL(capacity, 0) as capacity
                FROM Location 
                ORDER BY Location_ID
            """)
            
            self.locations = []
            location_details = {} 
            for row in cursor:
                self.locations.append(row[1])
                location_details[row[1]] = {
                    'id': row[0],
                    'capacity': row[2]
                }

            self.place_combobox['values'] = self.locations
            
            if not self.locations:
                messagebox.showwarning("تنبيه", "لم يتم إضافة أي أماكن بعد!")
                self.place_combobox.set('')
                
            return self.locations
            
        except pyodbc.Error as e:
            error_msg = f"فشل تحميل الأماكن:\n{str(e)}"
            if "Invalid column name" in str(e):
                error_msg += "\nهيكل جدول الأماكن غير متوافق مع التطبيق"
            messagebox.showerror("خطأ في قاعدة البيانات", error_msg)
            return []
        except Exception as e:
            messagebox.showerror("خطأ غير متوقع", f"حدث خطأ أثناء تحميل الأماكن: {str(e)}")
            return []
        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except Exception as e:
                print(f"Warning: Error closing resources - {str(e)}")
            self.place_combobox.update()


    def load_schedules_from_db(self):
        """تحميل الجداول من قاعدة البيانات مع معالجة المواد المشتركة"""
        conn = None
        try:
            conn = self.connect_db()
            if not conn:
                messagebox.showerror("خطأ", "فشل الاتصال بقاعدة البيانات")
                return
                
            cursor = conn.cursor()
            
            self.schedule_data = {}
            self.data_manager.schedule_data = self.schedule_data
            
            query = """
                SELECT 
                    d.Department_name,
                    d.Department_ID,
                    lv.Levels_name,
                    sch.day,
                    sch.start_time,
                    sch.end_time,
                    loc.Location_name,
                    c.Course_name,
                    lec.F_name + ' ' + lec.L_name AS lecturer_name,
                    gr.Group_Type,
                    gr.Group_Number,
                    gr.Group_ID,
                    c.Course_ID
                FROM schedule sch
                JOIN groups gr ON sch.group_id = gr.group_id
                JOIN department d ON sch.Department_ID = d.Department_ID
                JOIN levels lv ON gr.Levels_ID = lv.Levels_ID
                JOIN courses c ON gr.Course_ID = c.Course_ID
                JOIN lecturer lec ON gr.Lecturer_ID = lec.Lecturer_ID
                JOIN location loc ON sch.location_id = loc.location_id
                ORDER BY d.Department_name, lv.Levels_name, sch.day, sch.start_time
            """
            
            cursor.execute(query)
            schedules = cursor.fetchall()
            
            if not schedules:
                print("لا توجد جداول محفوظة في قاعدة البيانات")
                return
                
            for schedule in schedules:
                dept = schedule[0]
                dept_id = schedule[1]
                year = schedule[2]
                key = f"{dept}_{year}"
                
                if key not in self.schedule_data:
                    self.schedule_data[key] = {
                        'dept': dept,
                        'year': year,
                        'schedule': {}
                    }
                    
                day = schedule[3]
                if day not in self.schedule_data[key]['schedule']:
                    self.schedule_data[key]['schedule'][day] = []
                    
                is_shared = False
                if schedule[9] == 'lecture':
                    cursor.execute("SELECT COUNT(*) FROM Course_Department WHERE Course_ID = ?", (schedule[12],))
                    is_shared = cursor.fetchone()[0] > 1
                
                departments = [dept] if schedule[9] == 'practical' else self.get_shared_departments(schedule[12])
                
                self.schedule_data[key]['schedule'][day].append({
                    'start': schedule[4],
                    'end': schedule[5],
                    'place': schedule[6],
                    'group': {
                        'subject': schedule[7],
                        'instructor': schedule[8],
                        'Group_Type': schedule[9],
                        'group_number': schedule[10],
                        'group_id': schedule[11],
                        'departments': departments,
                        'year_level': year,
                        'dept_id': dept_id,
                        'course_id': schedule[12],
                        'is_shared': is_shared
                    }
                })
                
            print("تم تحميل الجداول بنجاح من قاعدة البيانات")
            
        except pyodbc.Error as e:
            messagebox.showerror("خطأ", f"فشل تحميل الجداول:\n{str(e)}")
        finally:
            if conn:
                conn.close()

    def delete_appointment_and_group(self, day, appt):
        if not messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذا الموعد؟"):
            return

        conn = None
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            
            # حذف من قاعدة البيانات
            delete_query = """
                DELETE FROM Schedule 
                WHERE Group_ID = ? 
                AND day = ? 
                AND start_time = ? 
                AND end_time = ?
            """
            cursor.execute(delete_query, (
                appt['group']['group_id'],
                day,
                appt['start'],
                appt['end']
            ))
            
            # تحديث البيانات المحلية
            schedule_key = f"{self.dept_combobox.get()}_{self.year_combobox.get()}"
            if schedule_key in self.schedule_data and day in self.schedule_data[schedule_key]['schedule']:
                self.schedule_data[schedule_key]['schedule'][day] = [
                    a for a in self.schedule_data[schedule_key]['schedule'][day] 
                    if not (a['start'] == appt['start'] and a['end'] == appt['end'])
                ]
            
            # إرجاع المجموعة للقائمة المتاحة
            group_data = appt['group']
            self.filtered_groups_data.append(group_data)
            self.update_group_combobox()
            
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف الموعد بنجاح")
            
            # تحديث الجدول
            self.refresh_schedule_table()
            
        except pyodbc.Error as e:
            if conn:
                conn.rollback()
            messagebox.showerror("خطأ في قاعدة البيانات", f"فشل حذف الموعد: {str(e)}")
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("خطأ غير متوقع", f"حدث خطأ غير متوقع: {str(e)}")
        finally:
            if conn:
                conn.close()

    def update_shared_courses(self):
        # update data of participated lectures between departs
        conn = None
        try:
            conn = self.connect_db()
            if not conn:
                return
                
            cursor = conn.cursor()
            
            # get the participated subjects
            cursor.execute("""
                SELECT Course_ID 
                FROM Course_Department
                GROUP BY Course_ID
                HAVING COUNT(*) > 1
            """)
            shared_courses = [row[0] for row in cursor.fetchall()]
            
            # update tables data of participated lectures between departs
            for course_id in shared_courses:
                cursor.execute("""
                    SELECT d.Department_name 
                    FROM Course_Department cd
                    JOIN Department d ON cd.Department_ID = d.Department_ID
                    WHERE cd.Course_ID = ?
                """, (course_id,))
                departments = [row[0] for row in cursor.fetchall()]
                
                # update time for tables data of participated lectures between departs
                for schedule_key, schedule_info in self.schedule_data.items():
                    for day, appointments in schedule_info['schedule'].items():
                        for appt in appointments:
                            if appt['group'].get('course_id') == course_id:
                                appt['group']['departments'] = departments
                                appt['group']['is_shared'] = True
                                
        except pyodbc.Error as e:
            messagebox.showerror("خطأ", f"فشل تحديث المواد المشتركة:\n{str(e)}")
        finally:
            if conn:
                conn.close()
                
    def get_shared_departments(self, course_id):
        conn = self.connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.Department_name 
                FROM Course_Department cd
                JOIN Department d ON cd.Department_ID = d.Department_ID
                WHERE cd.Course_ID = ?
            """, (course_id,))
            return [row[0] for row in cursor.fetchall()]
        except pyodbc.Error as e:
            messagebox.showerror("خطأ", f"تعذر جلب الأقسام المشتركة: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()

    def save_schedule(self, day, start, end, place, group):
        """حفظ الموعد في قاعدة البيانات مع معالجة المواد المشتركة بين الأقسام"""
        if not all([day, start, end, place, group]):
            messagebox.showerror("خطأ", "بيانات غير مكتملة!")
            return False

        try:
            # check day and time ----> have problem that the time un tables is reversed in the db
            if start >= end:
                messagebox.showerror("خطأ", "وقت البداية يجب أن يكون قبل وقت النهاية")
                return False

            if day not in self.days:
                messagebox.showerror("خطأ", f"اليوم يجب أن يكون من: {', '.join(self.days)}")
                return False

            conn = self.connect_db()
            if not conn:
                return False

            cursor = conn.cursor()

            # get place id
            cursor.execute("SELECT Location_ID FROM Location WHERE Location_name = ?", (place,))
            location_result = cursor.fetchone()
            if not location_result:
                messagebox.showerror("خطأ", "المكان المحدد غير موجود في قاعدة البيانات!")
                conn.close()
                return False
            location_id = location_result[0]

            # check conflicts
            lecturer_conflict_query = """
                SELECT 
                    s.schedule_id,
                    c.Course_name,
                    l.Location_name,
                    s.day,
                    s.start_time,
                    s.end_time,
                    d.Department_name
                FROM Schedule s
                JOIN Groups g ON s.Group_ID = g.Group_ID
                JOIN Courses c ON g.Course_ID = c.Course_ID
                JOIN Location l ON s.Location_ID = l.Location_ID
                JOIN Department d ON s.Department_ID = d.Department_ID
                WHERE g.Lecturer_ID = ?
                AND s.day = ?
                AND NOT (s.end_time <= ? OR s.start_time >= ?)
            """

            conflict_check_query = """
                SELECT 
                    s.schedule_id,
                    c.Course_name,
                    lec.F_name + ' ' + lec.L_name AS lecturer_name,
                    l.Location_name,
                    s.day,
                    s.start_time,
                    s.end_time
                FROM Schedule s
                JOIN Groups g ON s.Group_ID = g.Group_ID
                JOIN Courses c ON g.Course_ID = c.Course_ID
                JOIN Lecturer lec ON g.Lecturer_ID = lec.Lecturer_ID
                JOIN Location l ON s.Location_ID = l.Location_ID
                WHERE l.Location_name = ?
                AND s.day = ?
                AND NOT (s.end_time <= ? OR s.start_time >= ?)
            """

            # check conflicts before adding group
            conflicts_detected = False

            # participated lectures
            if group.get('is_shared', False) and group['Group_Type'] == 'lecture':
                shared_departments = self.get_shared_departments(group['course_id'])
                
                # lecturer conflict check
                cursor.execute(lecturer_conflict_query, (group['lecturer_id'], day, start, end))
                lecturer_conflicts = cursor.fetchall()
                if lecturer_conflicts:
                    conflict_details = "\n".join(
                        f"- {row[1]} في {row[2]} (قسم {row[6]}) - {row[3]} {row[4]}-{row[5]}"
                        for row in lecturer_conflicts
                    )
                    messagebox.showerror("تعارض في مواعيد المحاضر", f"المحاضر {group['instructor']} لديه مواعيد متضاربة:\n{conflict_details}")
                    conflicts_detected = True

                # place conflicts check ---> for all departs
                if not conflicts_detected:
                    for dept_name in shared_departments:
                        cursor.execute("SELECT Department_ID FROM Department WHERE Department_name = ?", (dept_name,))
                        dept_result = cursor.fetchone()
                        if not dept_result:
                            continue

                        cursor.execute(conflict_check_query, (place, day, start, end))
                        if cursor.fetchall():
                            messagebox.showerror("تعارض في المكان", f"المكان {place} محجوز بالفعل في هذا الوقت")
                            conflicts_detected = True
                            break

            # not participated groups
            else:
                # lecturer conflict check
                cursor.execute(lecturer_conflict_query, (group['lecturer_id'], day, start, end))
                lecturer_conflicts = cursor.fetchall()
                if lecturer_conflicts:
                    conflict_details = "\n".join(
                        f"- {row[1]} في {row[2]} (قسم {row[6]}) - {row[3]} {row[4]}-{row[5]}"
                        for row in lecturer_conflicts
                    )
                    messagebox.showerror("تعارض في مواعيد المحاضر", f"المحاضر {group['instructor']} لديه مواعيد متضاربة:\n{conflict_details}")
                    conflicts_detected = True

                # place conflict check
                if not conflicts_detected:
                    cursor.execute(conflict_check_query, (place, day, start, end))
                    if cursor.fetchall():
                        messagebox.showerror("تعارض في المكان", f"المكان {place} محجوز بالفعل في هذا الوقت")
                        conflicts_detected = True

            # if conflict ---> dont save
            if conflicts_detected:
                conn.rollback()
                conn.close()
                return False

            # add if no conflicts
            insert_query = """
                INSERT INTO Schedule 
                (Department_ID, Group_ID, Location_ID, day, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """

            # adding participated lectures
            if group.get('is_shared', False) and group['Group_Type'] == 'lecture':
                shared_departments = self.get_shared_departments(group['course_id'])
                for dept_name in shared_departments:
                    cursor.execute("SELECT Department_ID FROM Department WHERE Department_name = ?", (dept_name,))
                    dept_result = cursor.fetchone()
                    if not dept_result:
                        continue
                    dept_id = dept_result[0]

                    cursor.execute(insert_query, (dept_id, group['group_id'], location_id, day, start, end))

                    year = group['year_level']
                    schedule_key = f"{dept_name}_{year}"
                    if schedule_key not in self.schedule_data:
                        self.schedule_data[schedule_key] = {'dept': dept_name, 'year': year, 'schedule': {}}
                    if day not in self.schedule_data[schedule_key]['schedule']:
                        self.schedule_data[schedule_key]['schedule'][day] = []
                    
                    self.schedule_data[schedule_key]['schedule'][day].append({
                        'start': start,
                        'end': end,
                        'place': place,
                        'group': {
                            **group,
                            'departments': [dept_name],
                            'dept_id': dept_id,
                            'location_id': location_id
                        }
                    })

            else:
                cursor.execute(insert_query, (group['dept_id'], group['group_id'], location_id, day, start, end))
                self.update_local_schedule(day, start, end, place, group)

            conn.commit()
            messagebox.showinfo("نجاح", "تم حفظ الموعد بنجاح")
            return True

        except pyodbc.Error as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            error_msg = "خطأ في قاعدة البيانات: "
            if '2627' in str(e):
                error_msg += "هذا الموعد مسجل بالفعل"
            else:
                error_msg += str(e)
            messagebox.showerror("خطأ", error_msg)
            return False
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            messagebox.showerror("خطأ غير متوقع", f"حدث خطأ غير متوقع: {str(e)}")
            return False
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
                if 'conn' in locals() and conn:
                    conn.close()
            except Exception as e:
                print(f"حدث خطأ أثناء إغلاق الاتصال: {str(e)}")

    def get_current_dept_id(self):
        selected_dept = self.dept_combobox.get()
        if not selected_dept:
            return None
            
        conn = self.connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Department_ID FROM Department WHERE Department_name = ?", (selected_dept,))
            result = cursor.fetchone()
            return result[0] if result else None
        except pyodbc.Error as e:
            messagebox.showerror("خطأ", f"تعذر الحصول على معرف القسم: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()

    def load_saved_schedule(self):
        if not self.current_schedule_key:
            return

        current_dept = self.current_schedule_key.split('_')[0]
        
        schedule_info = self.schedule_data.get(self.current_schedule_key, {})
        for day, appointments in schedule_info.get('schedule', {}).items():
            for appt in appointments:
                if (appt['group']['Group_Type'] == 'lecture' and 
                    current_dept in appt['group']['departments']):
                    self._create_schedule_cell(day, appt)
                
                elif (appt['group']['Group_Type'] == 'practical' and 
                    current_dept in appt['group']['departments']):
                    self._create_schedule_cell(day, appt)

    def _create_schedule_cell(self, day, appt):
        try:
            start_col = self.times.index(appt['start'])
            duration = appt['end'] - appt['start']
            row_idx = self.days.index(day) + 1

            bg_color = "#d4edda" if appt['group']['Group_Type'] == 'lecture' else "#d4e6f1"
            cell_text = f"{appt['group']['subject']}\n{appt['group']['instructor']}\n{appt['place']}"
            
            if appt['group']['Group_Type'] == 'practical':
                group_num = appt['group'].get('group_number', '')
                cell_text = f"(عملي مجموعة {group_num})\n{cell_text}" if group_num else f"(عملي)\n{cell_text}"

            cell = tk.Label(
                self.table_frame, 
                text=cell_text, 
                bg=bg_color,
                fg="#333333",
                relief="solid", 
                width=15*duration, 
                height=3
            )
            cell.grid(row=row_idx, column=start_col, columnspan=duration, sticky="nsew")
            
            # ربط حدث النقر للحذف في وضع التعديل
            if self.edit_mode:
                cell.bind("<Button-1>", lambda e, d=day, a=appt: self.delete_appointment_and_group(d, a))
        except Exception as e:
            print(f"Error creating cell: {e}")

    def get_location_id(self, location_name):
        conn = self.connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Location_ID FROM Location WHERE Location_name=?", (location_name,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def update_local_schedule(self, day, start, end, place, group):
        schedule_key = f"{self.dept_combobox.get()}_{self.year_combobox.get()}"
        
        if schedule_key not in self.schedule_data:
            self.schedule_data[schedule_key] = {
                'dept': self.dept_combobox.get(),
                'year': self.year_combobox.get(),
                'schedule': {}
            }
        
        if day not in self.schedule_data[schedule_key]['schedule']:
            self.schedule_data[schedule_key]['schedule'][day] = []
        
        self.schedule_data[schedule_key]['schedule'][day].append({
            'start': start,
            'end': end,
            'place': place,
            'group': group
        })
        
        self.data_manager.schedule_data = self.schedule_data


    def validate_schedule_entry(self, day, start, end, place, group):
        errors = []
        
        if start >= end:
            errors.append("وقت البداية يجب أن يكون قبل وقت النهاية")
        
        if not day in self.days:
            errors.append(f"اليوم يجب أن يكون من: {', '.join(self.days)}")
        
        if place not in self.locations:
            errors.append("المكان غير صحيح")
            
        if errors:
            raise ValueError("\n".join(errors))

    def show_db_error(self, error):
        error_mapping = {
            '23000': "هذا الموعد مسجل بالفعل",
            '22001': "بيانات طويلة جداً",
            '08001': "تعذر الاتصال بالخادم"
        }
        msg = error_mapping.get(error.sqlstate, f"خطأ في قاعدة البيانات: {str(error)}")
        messagebox.showerror("خطأ", msg)

# class of show Data entry page


class DataEntryPage(tk.Frame):
    """صفحة إدخال البيانات """
    def __init__(self, parent, return_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.return_callback = return_callback
        
        # إعدادات التصميم
        self.BG_COLOR = "#f0f4f7"
        self.BUTTON_COLOR = "#3E546B"
        self.ACCENT_COLOR = "#2980b9"
        
        # إعدادات قاعدة البيانات
        self.SERVER = '.'
        self.DATABASE = 'project'
        
        self.setup_ui()
        self.setup_style()
    
    def setup_style(self):
        """إعداد النمط العام"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TNotebook', background=self.BG_COLOR, tabposition='ne')
        self.style.configure('TFrame', background=self.BG_COLOR)
        self.style.configure('TButton', background=self.BUTTON_COLOR, 
                           foreground='white', font=('Arial', 12))
        self.style.map('TButton', background=[('active', self.ACCENT_COLOR)])
        self.style.configure('Treeview', font=('Arial', 11), rowheight=25)
        self.style.configure('Treeview.Heading', font=('Arial', 12, 'bold'))
        self.style.configure('Rounded.TButton', background=self.BUTTON_COLOR,
                           foreground='white', borderwidth=0, bordercolor='#2ecc71',
                           focusthickness=3, focuscolor='none', font=('Arial', 12, 'bold'))
        self.style.configure('Accent.TButton', background=self.ACCENT_COLOR, 
                           foreground='white', font=('Arial', 12, 'bold'))
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # إنشاء نوافذ التبويب
        self.notebook = ttk.Notebook(self)
        self.tabs = {
            "Courses": ttk.Frame(self.notebook),
            "Department": ttk.Frame(self.notebook),
            "Lecturer": ttk.Frame(self.notebook),
            "Location": ttk.Frame(self.notebook)
        }
        
        # إضافة التبويبات
        self.notebook.add(self.tabs["Location"], text="📍 الأماكن")
        self.notebook.add(self.tabs["Lecturer"], text="👨 أعضاء التدريس")
        self.notebook.add(self.tabs["Department"], text="📊 البرامج")
        self.notebook.add(self.tabs["Courses"], text="📚 المقررات")
        self.notebook.pack(expand=True, fill='both', padx=15, pady=15)
        
        # إعداد كل تبويب
        self.setup_courses_tab()
        self.setup_department_tab()
        self.setup_lecturer_tab()
        self.setup_location_tab()
        # return to main page
        back_button = ttk.Button(
            self,
            text="العودة للرئيسية",
            command=self.return_callback,
            style='Rounded.TButton'
        )
        back_button.pack(pady=20)
        # زر العودة للصفحة الرئيسية 
        back_frame = ttk.Frame(self, style='TFrame')
        back_frame.pack(fill='x', pady=10, padx=10)

        back_button = ttk.Button(
            back_frame, 
            text="🏠 العودة للرئيسية", 
            command=self.return_callback,
            style='Accent.TButton',
            width=20
        )
        back_button.pack(side='right', padx=10)
    
    def setup_courses_tab(self):
        """إعداد تبويب المقررات"""
        self.courses_fields = {
            'Course_ID': ': ID',
            'Course_name': ': اسم المقرر',
            'code': ': كود المقرر',
            'Lecture_hours': ': عدد ساعات المحاضره',
            'Levels_ID': ':المستوى',
            'Practical_hours': ':عدد ساعات العملى',
            'Exercise_hours': ':عدد ساعات التمرين'
        }
        self.courses_entries = self.create_input_section(self.tabs["Courses"], self.courses_fields)

        # إطار التحكم والبحث
        control_frame = ttk.Frame(self.tabs["Courses"])
        control_frame.pack(pady=10, fill='x', padx=20)

        # أزرار التحكم
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="⟳ تحديث البيانات", 
                  command=lambda: self.generic_refresh('Courses', self.tree_courses)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 حذف", 
                  command=lambda: self.delete_handler('Courses', self.tree_courses)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 تعديل",
                  command=lambda: self.update_handler('Courses', self.courses_entries, self.tree_courses, self.courses_fields)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="➕ إضافة",
                  command=lambda: self.generic_operation('Courses', self.courses_entries, self.tree_courses, self.courses_fields, 'add')).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧹 مسح الحقول", 
                  command=lambda: self.clear_entries(self.courses_entries)).pack(side=tk.LEFT, padx=5)

        # حقل البحث
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)

        self.search_entry_courses = ttk.Entry(search_frame, font=('Arial', 12), width=20)
        self.search_entry_courses.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="🔍بحث", command=self.search_courses, width=5).pack(side=tk.LEFT)

        # الجدول
        self.tree_courses = self.create_table(self.tabs["Courses"], [
            'Course_ID', 'Course_name', 'code', 'Lecture_hours', 'Levels_name',
            'Practical_hours', 'Exercise_hours'
        ])
        self.generic_refresh('Courses', self.tree_courses)
        self.tree_courses.bind("<<TreeviewSelect>>", lambda e: self.fill_entries_from_selection(self.tree_courses, self.courses_entries))
    
    def setup_department_tab(self):
        """إعداد تبويب الأقسام"""
        self.department_fields = {
            'Department_ID': ' : ID',
            'Department_name': ':برنامج'
        }
        self.department_entries = self.create_input_section(self.tabs["Department"], self.department_fields)

        # إطار التحكم والبحث
        control_frame = ttk.Frame(self.tabs["Department"])
        control_frame.pack(pady=10, fill='x', padx=20)

        # أزرار التحكم
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="⟳ تحديث البيانات",
                command=lambda: self.generic_refresh('Department', self.tree_department)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 حذف", 
                command=lambda: self.delete_handler('Department', self.tree_department)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 تعديل",
                command=lambda: self.update_handler('Department', self.department_entries, self.tree_department, self.department_fields)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="➕ إضافة", 
                command=self.add_department).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧹 مسح الحقول", 
                command=lambda: self.clear_entries(self.department_entries)).pack(side=tk.LEFT, padx=5)

        # حقل البحث
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)

        self.search_entry_department = ttk.Entry(search_frame, font=('Arial', 12), width=20)
        self.search_entry_department.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="🔍بحث", command=self.search_departments, width=5).pack(side=tk.LEFT)

        # الجدول
        self.tree_department = self.create_table(self.tabs["Department"], ['Department_ID', 'Department_name'])
        self.generic_refresh('Department', self.tree_department)
        self.tree_department.bind("<<TreeviewSelect>>", lambda e: self.fill_entries_from_selection(self.tree_department, self.department_entries))
    
    def setup_lecturer_tab(self):
        """إعداد تبويب المحاضرين"""
        self.lecturer_fields = {
            'Lecturer_ID': ': ID',
            'F_name': ': اسم الدكتور الاول',
            'L_name': ':اسم الدكتور الثانى',
            'Department_ID': ': البرنامج'
        }
        self.lecturer_entries = self.create_input_section(self.tabs["Lecturer"], self.lecturer_fields)

        # إطار التحكم والبحث
        control_frame = ttk.Frame(self.tabs["Lecturer"])
        control_frame.pack(pady=10, fill='x', padx=20)

        # أزرار التحكم
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="⟳ تحديث البيانات", 
                  command=lambda: self.generic_refresh('Lecturer', self.tree_lecturer)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 حذف", 
                  command=lambda: self.delete_handler('Lecturer', self.tree_lecturer)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 تعديل",
                  command=lambda: self.update_handler('Lecturer', self.lecturer_entries, self.tree_lecturer, self.lecturer_fields)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="➕ إضافة",
                  command=lambda: self.generic_operation('Lecturer', self.lecturer_entries, self.tree_lecturer, self.lecturer_fields, 'add')).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧹 مسح الحقول", 
                  command=lambda: self.clear_entries(self.lecturer_entries)).pack(side=tk.LEFT, padx=5)

        # حقل البحث
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)

        self.search_entry_lecturer = ttk.Entry(search_frame, font=('Arial', 12), width=20)
        self.search_entry_lecturer.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="🔍بحث", command=self.search_lecturers, width=5).pack(side=tk.LEFT)

        # الجدول
        self.tree_lecturer = self.create_table(self.tabs["Lecturer"], ['Lecturer_ID', 'Full_name', 'Department_name'])
        self.generic_refresh('Lecturer', self.tree_lecturer)
        self.tree_lecturer.bind("<<TreeviewSelect>>", lambda e: self.fill_entries_from_selection(self.tree_lecturer, self.lecturer_entries))
    
    def setup_location_tab(self):
        """إعداد تبويب الأماكن"""
        self.place_fields = {
            'Location_ID': ': ID',
            'Location_name': ':اسم المكان',
            'capacity': ':السعه'
        }
        self.place_entries = self.create_input_section(self.tabs["Location"], self.place_fields)

        # إطار التحكم والبحث
        control_frame = ttk.Frame(self.tabs["Location"])
        control_frame.pack(pady=10, fill='x', padx=20)

        # أزرار التحكم
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="⟳ تحديث البيانات", 
                  command=lambda: self.generic_refresh('Location', self.tree_place)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 حذف", 
                  command=lambda: self.delete_handler('Location', self.tree_place)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 تعديل",
                  command=lambda: self.update_handler('Location', self.place_entries, self.tree_place, self.place_fields)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="➕ إضافة",
                  command=lambda: self.generic_operation('Location', self.place_entries, self.tree_place, self.place_fields, 'add')).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧹 مسح الحقول", 
                  command=lambda: self.clear_entries(self.place_entries)).pack(side=tk.LEFT, padx=5)

        # حقل البحث
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)

        self.search_entry_place = ttk.Entry(search_frame, font=('Arial', 12), width=20)
        self.search_entry_place.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="🔍بحث", command=self.search_locations, width=5).pack(side=tk.LEFT)

        # الجدول
        self.tree_place = self.create_table(self.tabs["Location"], list(self.place_fields.keys()))
        self.generic_refresh('Location', self.tree_place)
        self.tree_place.bind("<<TreeviewSelect>>", lambda e: self.fill_entries_from_selection(self.tree_place, self.place_entries))
    
    # ========== الدوال المساعدة ==========
    
    def create_input_section(self, parent, fields):
        frame = ttk.Frame(parent)
        frame.pack(pady=20, padx=20, fill='x')
        entries = {}
        for i, (field, label) in enumerate(fields.items()):
            ttk.Label(frame, text=label, font=('Arial', 12), background=self.BG_COLOR).grid(row=i, column=2, padx=5, pady=5, sticky='nw')

            if field == 'Levels_ID':
                entries[field] = ttk.Combobox(frame, font=('Arial', 12))
                self.load_levels(entries[field])
            elif field == 'Department_ID' and parent != self.tabs["Department"]:
                entries[field] = ttk.Combobox(frame, font=('Arial', 12))
                self.load_departments(entries[field])
            else:
                entries[field] = ttk.Entry(frame, font=('Arial', 12))

            entries[field].grid(row=i, column=1, padx=5, pady=5, sticky='n')
            frame.columnconfigure(0, weight=1)
        
        if parent == self.tabs["Courses"]:
            entries['Lecture_hours'] = ttk.Combobox(frame, values=['0', '1', '2', '3','4'], font=('Arial', 12))
            entries['Lecture_hours'].grid(row=3, column=1, padx=5, pady=5, sticky='n')
            
            entries['Practical_hours'] = ttk.Combobox(frame, values=['0', '1', '2', '3'], font=('Arial', 12))
            entries['Practical_hours'].grid(row=5, column=1, padx=5, pady=5, sticky='n')
            
            entries['Exercise_hours'] = ttk.Combobox(frame, values=['0', '1', '2', '3'], font=('Arial', 12))
            entries['Exercise_hours'].grid(row=6, column=1, padx=5, pady=5, sticky='n')
        
        return entries
    
    def create_table(self, parent, columns):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')
        
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        
        return tree
    
    def load_levels(self, combobox):
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Levels_name FROM Levels")
                combobox['values'] = [row[0] for row in cursor.fetchall()]
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل تحميل المستويات: {str(e)}")
            finally:
                conn.close()
    
    def load_departments(self, combobox):
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Department_name FROM Department")
                combobox['values'] = [row[0] for row in cursor.fetchall()]
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل تحميل الأقسام: {str(e)}")
            finally:
                conn.close()
    
    def fill_entries_from_selection(self, tree, entries):
        selected = tree.selection()
        if not selected:
            return
        
        values = tree.item(selected[0], 'values')
        try:
            if 'F_name' in entries and 'L_name' in entries:  # حالة المحاضرين
                full_name = values[1].strip().split(' ', 1)
                entries['F_name'].delete(0, tk.END)
                entries['F_name'].insert(0, full_name[0] if len(full_name) > 0 else '')
                entries['L_name'].delete(0, tk.END)
                entries['L_name'].insert(0, full_name[1] if len(full_name) > 1 else '')
                entries['Lecturer_ID'].delete(0, tk.END)
                entries['Lecturer_ID'].insert(0, values[0])
                if 'Department_ID' in entries:
                    entries['Department_ID'].set(values[2])
            elif 'Levels_ID' in entries:  # حالة المقررات
                for key, entry in entries.items():
                    if key == 'Levels_ID':
                        entry.set(values[4])
                    elif key == 'Lecture_hours':
                        entry.set(values[3] if values[3] != 'None' else '0')
                    elif key == 'Practical_hours':
                        entry.set(values[5] if values[5] != 'None' else '0')
                    elif key == 'Exercise_hours':
                        entry.set(values[6] if values[6] != 'None' else '0')
                    else:
                        idx = list(entries.keys()).index(key)
                        if idx < len(values):
                            if isinstance(entry, ttk.Entry):
                                entry.delete(0, tk.END)
                                entry.insert(0, values[idx])
                            elif isinstance(entry, ttk.Combobox):
                                entry.set(values[idx])
            else:
                for key, entry in entries.items():
                    idx = list(entries.keys()).index(key)
                    if idx < len(values):
                        if isinstance(entry, ttk.Entry):
                            entry.delete(0, tk.END)
                            entry.insert(0, values[idx])
                        elif isinstance(entry, ttk.Combobox):
                            entry.set(values[idx])
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تعبئة الحقول: {str(e)}")
    
    def clear_entries(self, entries):
        for entry in entries.values():
            if isinstance(entry, ttk.Combobox):
                entry.set('')
            else:
                entry.delete(0, tk.END)
    
    def connect_db(self):
        try:
            # الحصول على إعدادات الاتصال من الصفحة الرئيسية
            main_page = self.master.master if isinstance(self.master, tk.Toplevel) else self.master
            if hasattr(main_page, 'db_server') and hasattr(main_page, 'db_name'):
                server = main_page.db_server
                database = main_page.db_name
            else:
                server = '.'
                database = 'project'
            
            conn = pyodbc.connect(
                f'DRIVER={{SQL Server}};SERVER={server};'
                f'DATABASE={database};Trusted_Connection=yes;'
                )
            return conn
        except pyodbc.Error as e:
            messagebox.showerror("خطأ في الاتصال", f"فشل الاتصال بقاعدة البيانات:\n{str(e)}")
            return None
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")
            return None
    
    def get_level_id(self, level_name):
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Levels_ID FROM Levels WHERE Levels_name=?", (level_name,))
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل الحصول على رقم المستوى: {str(e)}")
                return None
            finally:
                conn.close()
        return None
    
    def get_department_id(self, department_name):
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Department_ID FROM Department WHERE Department_name=?", (department_name,))
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل الحصول على رقم القسم: {str(e)}")
                return None
            finally:
                conn.close()
        return None
    
    def update_department_comboboxes(self):
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Department_name FROM Department")
                departments = [row[0] for row in cursor.fetchall()]
                
                # تحديث Combobox الأقسام في جميع النوافذ
                for tab in self.tabs.values():
                    for child in tab.winfo_children():
                        if isinstance(child, ttk.Frame):
                            for entry in child.winfo_children():
                                if isinstance(entry, ttk.Combobox) and 'Department_ID' in str(entry):
                                    entry['values'] = departments
            except Exception as e:
                print(f"حدث خطأ أثناء تحديث الأقسام: {str(e)}")
            finally:
                conn.close()
    
    # ========== دوال البحث ==========
    
    def search_courses(self):
        search_term = self.search_entry_courses.get().strip()
        if not search_term:
            self.generic_refresh('Courses', self.tree_courses)
            return
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT C.Course_ID, C.Course_name, C.code, 
                           CASE WHEN C.Lecture_hours IS NULL THEN 'None' ELSE CAST(C.Lecture_hours AS varchar) END,
                           L.Levels_name,
                           CASE WHEN C.Practical_hours IS NULL THEN 'None' ELSE CAST(C.Practical_hours AS varchar) END,
                           CASE WHEN C.Exercise_hours IS NULL THEN 'None' ELSE CAST(C.Exercise_hours AS varchar) END
                    FROM Courses C
                    JOIN Levels L ON C.Levels_ID = L.Levels_ID
                    WHERE C.Course_name LIKE ? OR C.code LIKE ? OR C.Course_ID LIKE ?
                """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
                
                self.tree_courses.delete(*self.tree_courses.get_children())
                rows = cursor.fetchall()
                if not rows:
                    messagebox.showinfo("بحث", "لا توجد نتائج مطابقة للبحث")
                for row in rows:
                    self.tree_courses.insert("", tk.END, values=[str(item) for item in row])
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل البحث: {str(e)}")
            finally:
                conn.close()
    
    def search_departments(self):
        search_term = self.search_entry_department.get().strip()
        if not search_term:
            self.generic_refresh('Department', self.tree_department)
            return
        
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT Department_ID, Department_name 
                    FROM Department
                    WHERE Department_name LIKE ? OR Department_ID LIKE ?
                """, (f'%{search_term}%', f'%{search_term}%'))
                
                self.tree_department.delete(*self.tree_department.get_children())
                rows = cursor.fetchall()
                if not rows:
                    messagebox.showinfo("بحث", "لا توجد نتائج مطابقة للبحث")
                for row in rows:
                    self.tree_department.insert("", tk.END, values=[str(item) for item in row])
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل البحث: {str(e)}")
            finally:
                conn.close()
    
    def search_lecturers(self):
        search_term = self.search_entry_lecturer.get().strip()
        if not search_term:
            self.generic_refresh('Lecturer', self.tree_lecturer)
            return
        
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT L.Lecturer_ID, L.F_name + ' ' + L.L_name AS Full_name, D.Department_name
                    FROM Lecturer L
                    JOIN Department D ON L.Department_ID = D.Department_ID
                    WHERE L.F_name LIKE ? OR L.L_name LIKE ? OR D.Department_name LIKE ? OR L.Lecturer_ID LIKE ?
                """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
                
                self.tree_lecturer.delete(*self.tree_lecturer.get_children())
                rows = cursor.fetchall()
                if not rows:
                    messagebox.showinfo("بحث", "لا توجد نتائج مطابقة للبحث")
                for row in rows:
                    self.tree_lecturer.insert("", tk.END, values=[str(item) for item in row])
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل البحث: {str(e)}")
            finally:
                conn.close()
    
    def search_locations(self):
        search_term = self.search_entry_place.get().strip()
        if not search_term:
            self.generic_refresh('Location', self.tree_place)
            return
        
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT Location_ID, Location_name, capacity
                    FROM Location
                    WHERE Location_name LIKE ? OR Location_ID LIKE ?
                """, (f'%{search_term}%', f'%{search_term}%'))
                
                self.tree_place.delete(*self.tree_place.get_children())
                rows = cursor.fetchall()
                if not rows:
                    messagebox.showinfo("بحث", "لا توجد نتائج مطابقة للبحث")
                for row in rows:
                    self.tree_place.insert("", tk.END, values=[str(item) for item in row])
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل البحث: {str(e)}")
            finally:
                conn.close()
    
    # ========== دوال العمليات الأساسية ==========
    
    def generic_refresh(self, table_name, tree):
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                if table_name == 'Lecturer':
                    cursor.execute("""
                        SELECT L.Lecturer_ID, L.F_name + ' ' + L.L_name AS Full_name, D.Department_name
                        FROM Lecturer L
                        JOIN Department D ON L.Department_ID = D.Department_ID
                    """)
                elif table_name == 'Courses':
                    cursor.execute("""
                        SELECT C.Course_ID, C.Course_name, C.code, 
                               CASE WHEN C.Lecture_hours IS NULL THEN 'None' ELSE CAST(C.Lecture_hours AS varchar) END,
                               L.Levels_name,
                               CASE WHEN C.Practical_hours IS NULL THEN 'None' ELSE CAST(C.Practical_hours AS varchar) END,
                               CASE WHEN C.Exercise_hours IS NULL THEN 'None' ELSE CAST(C.Exercise_hours AS varchar) END
                        FROM Courses C
                        JOIN Levels L ON C.Levels_ID = L.Levels_ID
                    """)
                elif table_name == 'Department':
                    cursor.execute("SELECT Department_ID, Department_name FROM Department")
                else:
                    cursor.execute(f"SELECT * FROM {table_name}")
                
                tree.delete(*tree.get_children())
                rows = cursor.fetchall()
                for row in rows:
                    tree.insert("", tk.END, values=[str(item) for item in row])
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل التحديث: {str(e)}")
            finally:
                conn.close()
    
    def generic_operation(self, table_name, entries, tree, fields, operation, record_id=None):
        if table_name == 'Department' and operation == 'add':
            self.add_department()
            return
        
        id_columns = {
            'Courses': 'Course_ID',
            'Lecturer': 'Lecturer_ID',
            'Location': 'Location_ID',
            'Department': 'Department_ID'
        }
        pk = id_columns.get(table_name, 'id')

        conn = self.connect_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            values = []
            if operation in ['add', 'update'] and fields:
                for field, entry in entries.items():
                    val = entry.get() if isinstance(entry, (ttk.Entry, ttk.Combobox)) else ''
                    
                    if not val and field in ['Course_ID', 'Lecturer_ID', 'Location_ID']:
                        messagebox.showerror("خطأ", f"الحقل {fields[field]} مطلوب")
                        return
                    
                    # معالجة خاصة لجميع أنواع الساعات
                    if field in ['Lecture_hours', 'Practical_hours', 'Exercise_hours']:
                        if val == '0':
                            val = None
                        else:
                            try:
                                val = int(val) if val else None
                            except ValueError:
                                messagebox.showerror("خطأ", f"قيمة غير صالحة لـ {fields[field]}")
                                return
                    elif field == 'Levels_ID':
                        level_name = val
                        level_id = self.get_level_id(level_name)
                        if level_id is None:
                            messagebox.showerror("خطأ", "المستوى المحدد غير موجود")
                            return
                        val = level_id
                    elif field == 'Department_ID' and table_name != 'Department':
                        dept_name = val
                        dept_id = self.get_department_id(dept_name)
                        if dept_id is None:
                            messagebox.showerror("خطأ", "القسم المحدد غير موجود")
                            return
                        val = dept_id
                    else:
                        if field in ['Course_ID', 'Lecturer_ID', 'Location_ID', 'capacity']:
                            try:
                                val = int(val) if val else 0
                            except ValueError:
                                messagebox.showerror("خطأ", f"قيمة غير صالحة لـ {fields[field]}")
                                return
                    values.append(val)

            if operation == 'add' and fields:
                placeholders = ','.join(['?'] * len(values))
                columns = ','.join(fields.keys())
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(query, values)
                
            elif operation == 'update' and fields:
                set_clause = ', '.join([f"{k}=?" for k in fields.keys()])
                values.append(record_id)
                cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {pk}=?", values)
                
            elif operation == 'delete':
                cursor.execute(f"DELETE FROM {table_name} WHERE {pk}=?", (record_id,))
                
            conn.commit()
            messagebox.showinfo("نجاح", "تم تنفيذ العملية بنجاح")
            
            self.generic_refresh(table_name, tree)
            if entries:
                self.clear_entries(entries)
                
        except pyodbc.Error as e:
            conn.rollback()
            messagebox.showerror("خطأ في قاعدة البيانات", f"فشل العملية: {str(e)}")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def add_department(self):
        dept_id = self.department_entries['Department_ID'].get()
        dept_name = self.department_entries['Department_name'].get()
        
        if not dept_id or not dept_name:
            messagebox.showerror("خطأ", "جميع الحقول مطلوبة!")
            return
        
        try:
            dept_id = int(dept_id)
        except ValueError:
            messagebox.showerror("خطأ", "رقم القسم يجب أن يكون رقماً صحيحاً")
            return
        
        conn = self.connect_db()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # التحقق من عدم وجود القسم مسبقاً
            cursor.execute("SELECT 1 FROM Department WHERE Department_ID=?", (dept_id,))
            if cursor.fetchone():
                messagebox.showerror("خطأ", "رقم القسم موجود مسبقاً!")
                return
                
            cursor.execute(
                "INSERT INTO Department (Department_ID, Department_name) VALUES (?, ?)",
                (dept_id, dept_name)
            )
            conn.commit()
            messagebox.showinfo("نجاح", "تمت إضافة القسم بنجاح")
            
            # تحديث الجدول
            self.generic_refresh('Department', self.tree_department)
            self.clear_entries(self.department_entries)
            
            # تحديث Combobox الأقسام في الخلفية
            self.after(100, self.update_department_comboboxes)
            
        except pyodbc.Error as e:
            conn.rollback()
            messagebox.showerror("خطأ في قاعدة البيانات", f"فشل الإضافة: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def update_handler(self, table_name, entries, tree, fields):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار عنصر من الجدول")
            return
        record_id = tree.item(selected[0], 'values')[0]
        self.generic_operation(table_name, entries, tree, fields, 'update', record_id)
    
    def delete_handler(self, table_name, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء اختيار عنصر من الجدول")
            return
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من الحذف؟"):
            record_id = tree.item(selected[0], 'values')[0]
            self.generic_operation(table_name, None, tree, None, 'delete', record_id)
    
    def on_key_press(self, event):
        if event.keysym == 'Delete':
            current_tab = self.notebook.index(self.notebook.select())
            tab_name = list(self.tabs.keys())[current_tab]
            if tab_name == 'Courses':
                self.delete_handler('Courses', self.tree_courses)
            elif tab_name == 'Department':
                self.delete_handler('Department', self.tree_department)
            elif tab_name == 'Lecturer':
                self.delete_handler('Lecturer', self.tree_lecturer)
            elif tab_name == 'Location':
                self.delete_handler('Location', self.tree_place)
                
                
                
# Class of show table page
class Database:
    def __init__(self):
        # الحصول على إعدادات الاتصال من الصفحة الرئيسية
        root = tk.Tk()  # الحصول على النافذة الرئيسية
        root.withdraw()  # إخفاء النافذة
        
        for widget in root.winfo_children():
            if isinstance(widget, MainPage):
                main_page = widget
                break
        else:
            main_page = None
            
        if main_page and hasattr(main_page, 'db_server') and hasattr(main_page, 'db_name'):
            server = main_page.db_server
            database = main_page.db_name
        else:
            server = '.'
            database = 'project'
            
        self.connection = pyodbc.connect(
            f'DRIVER={{SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
        )
        self.cursor = self.connection.cursor()
    
    def __del__(self):
        self.connection.close()

    def get_study_schedule(self, department_id, level_id):
        query = """
        SELECT 
            s.day, 
            s.start_time, 
            s.end_time,
            c.Course_name AS subject,
            loc.Location_name AS place,
            l.F_name + ' ' + l.L_name AS instructor,
            g.Group_Type
        FROM Schedule s
        JOIN Groups g ON s.Group_ID = g.Group_ID
        JOIN Courses c ON g.Course_ID = c.Course_ID
        JOIN Lecturer l ON g.Lecturer_ID = l.Lecturer_ID
        JOIN Location loc ON s.Location_ID = loc.Location_ID
        JOIN Department d ON s.Department_ID = d.Department_ID
        JOIN Levels lvl ON g.Levels_ID = lvl.Levels_ID
        WHERE d.Department_ID = ? AND lvl.Levels_ID = ?
        ORDER BY s.day, s.start_time
        """
        self.cursor.execute(query, (department_id, level_id))
        return self.cursor.fetchall()
    
class StudyTablesPage(BasePage):
    """Class for viewing study tables"""
    def __init__(self, parent, return_callback):
        super().__init__(parent, return_callback)
        
        # Load search icon
        original_image = Image.open("search_icon8.png")
        resized_image = original_image.resize((40, 40))
        self.image = ImageTk.PhotoImage(resized_image)

        # search name  
        self.result_title_label = None  
        self.current_search_result = "" 
        self.current_mode = None
        self.table_frames = {
            'study': None,
            'teacher': None,
            'place': None
        }
        self.setup_ui()

    def setup_ui(self):
        buttons_frame = tk.Frame(self, bg=MAIN_PAGE_BUTTONS_HOVER)
        buttons_frame.pack(fill="x", pady=5)

        back_button = tk.Button(
            self,  # نضعه مباشرة في النافذة الرئيسية (self)
            text="العودة للرئيسية",
            command=self.return_callback,
            font=("Arial", 12),
            padx=20,
            pady=10
        )
        back_button.pack(side="bottom", pady=10) 

        self.main_frame = tk.Frame(self, bg=MAIN_PAGE_BUTTONS_FRAME_COLOR)
        self.main_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(
                buttons_frame,
                text="طباعة الجدول",
                font=("cairo", 14, "bold"),
                command=self.print_schedule,
                fg_color="#FF5733",  # لون مميز للزر
                hover_color="#C70039",
                border_width=0,
                corner_radius=6,
                text_color="white",
                height=45,
                width=200
            ).pack(side="left", padx=10, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="عرض جدول دراسي",
            font=("cairo", 14, "bold"),
            command=self.show_study_schedule,
            fg_color="#2CC985",
            hover_color="#207A4D",
            border_width=0,
            corner_radius=6,
            text_color="white",
            height=45,
            width=200
        ).pack(side="right", padx=10, pady=5, expand=True)

        ctk.CTkButton(
            buttons_frame,
            text="عرض جدول عضو هيئة تدريس",
            font=("cairo", 14, "bold"),
            command=self.show_teacher_schedule,
            fg_color="#4B7EBF",
            hover_color="#32527B",
            border_width=0,
            corner_radius=6,
            text_color="white",
            height=45,
            width=200
        ).pack(side="right", padx=10, pady=5, expand=True)

        ctk.CTkButton(
            buttons_frame,
            text="عرض جدول مكان",
            font=("cairo", 14, "bold"),
            command=self.show_place_schedule,
            fg_color="#4B7EBF",
            hover_color="#32527B",
            border_width=0,
            corner_radius=6,
            text_color="white",
            height=45,
            width=200
        ).pack(side="right", padx=10, pady=5, expand=True)

        self.main_frame = tk.Frame(self, bg=MAIN_PAGE_BUTTONS_FRAME_COLOR)
        self.main_frame.pack(fill="x", pady=5)
        
        self.results_container = tk.Frame(self, bg=MAIN_PAGE_BUTTONS_FRAME_COLOR)
        self.results_container.pack(fill="both", expand=True, padx=10, pady=10)

        
    def reset_dropdowns(self):
        self.department_var.set("القسم")
        self.year_var.set("المستوي")

    def update_result_title(self, title_text):
        """تحديث عنوان نتيجة البحث فوق الجدول"""
        if self.result_title_label is not None:
            self.result_title_label.destroy()
        
        self.current_search_result = title_text
        
        self.result_title_label = tk.Label(
            self.results_container,
            text=title_text,
            font=("Arial", 14, "bold"),
            bg=MAIN_PAGE_BUTTONS_FRAME_COLOR,
            fg="#2a52be"
        )
        self.result_title_label.pack(fill="x", pady=(5, 10), before=self.table_frames[self.current_mode])
        
    def show_study_schedule(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.current_mode = 'study'

        self.main_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.department_var = tk.StringVar(value="القسم")
        # استبدال القائمة الثابتة بالدالة التي تجلب الأقسام من قاعدة البيانات
        department_menu = ctk.CTkComboBox(
            self.main_frame,
            values=self.get_departments_from_db(),  # <-- التعديل هنا
            variable=self.department_var,
            state="readonly",
            width=200,
            height=35,
            dropdown_fg_color="white",
            dropdown_text_color="black",
            fg_color="#4B7EBF",
            text_color="white",
            corner_radius=6,
            justify="right",
            font=("Arial", 14, "bold")
        )
        department_menu.grid(row=0, column=3, padx=80, pady=10, sticky="e")

        self.year_var = tk.StringVar(value=" المستوي")
        val = ["المستوي الأول", "المستوي الثاني", "المستوي الثالث", "المستوي الرابع"]
        year_menu = ctk.CTkComboBox(
            self.main_frame,
            values=val,
            variable=self.year_var,
            state="readonly",
            width=200,
            height=35,
            dropdown_fg_color="white",
            dropdown_text_color="black",
            fg_color="#4B7EBF",
            text_color="white",
            corner_radius=6,
            justify="right",
            font=("Arial", 14, "bold")
        )
        year_menu.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        search_button = tk.Button(
            self.main_frame, 
            text="بحث",
            command=self.search_schedule,
            fg="white",
            font=("Arial", 12, "bold"),
            image=self.image
        )
        search_button.grid(row=0, column=0, padx=10, pady=10, sticky="e")

        if not self.table_frames['study']:
            self.table_frames['study'] = tk.Frame(self.results_container, bg=MAIN_PAGE_BUTTONS_FRAME_COLOR)
        for key in self.table_frames:
            if key != 'study' and self.table_frames[key] is not None:
                self.table_frames[key].pack_forget()
        self.table_frames['study'].pack(fill="both", expand=True)

    def show_teacher_schedule(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.current_mode = 'teacher'

        self.teacher_var = tk.StringVar(value="اختر المحاضر")
        teachers = self.get_teachers_from_db()

        teacher_combo = ttk.Combobox(
            self.main_frame,
            textvariable=self.teacher_var,
            values=teachers,
            state="readonly",
            width=28,
            font=("Arial", 14),
            justify="right"
        )

        teacher_combo.pack(side="right", padx=10, pady=5)


        # search button
        ctk.CTkButton(
            self.main_frame,
            text="بحث", 
            font=("cairo", 14, "bold"), 
            command=self.search_teacher_schedule,
            fg_color="#4B7EBF",
            hover_color="#32527B",
            border_width=0,
            corner_radius=6,
            text_color="white",
            height=45,
            width=200
        ).pack(side="right", padx=10, pady=5)

        if not self.table_frames['teacher']:
            self.table_frames['teacher'] = tk.Frame(self.results_container, bg=MAIN_PAGE_BUTTONS_FRAME_COLOR)
        for key in self.table_frames:
            if key != 'teacher' and self.table_frames[key] is not None:
                self.table_frames[key].pack_forget()
        self.table_frames['teacher'].pack(fill="both", expand=True)

    def get_teachers_from_db(self):
        try:
            db = Database()
            query = "SELECT Lecturer_ID, F_name + ' ' + L_name AS full_name FROM Lecturer ORDER BY full_name"
            db.cursor.execute(query)
            teachers = [f"{row[1]} (ID:{row[0]})" for row in db.cursor.fetchall()]
            return teachers if teachers else ["لا يوجد محاضرون مسجلون"]
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ في جلب قائمة المحاضرين: {str(e)}")
            return ["خطأ في جلب البيانات"]
        finally:
            db.connection.close()


    def format_teacher_schedule_data(self, db_data):
        formatted = {}
        days_order = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
        
        for day in days_order:
            formatted[day] = []
        
        for row in db_data:
            day, start_time, end_time, subject, place, departments, level, group_type = row
            formatted[day].append({
                'start': start_time,
                'end': end_time,
                'place': place,
                'group': {
                    'subject': subject,
                    'departments': departments,
                    'level': level,
                    'Group_Type': group_type.lower()
                }
            })
        
        return formatted

    def show_place_schedule(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.current_mode = 'place'

        # إنشاء ComboBox لعرض قائمة الأماكن
        self.place_var = tk.StringVar(value="اختر المكان")
        places = self.get_places_from_db() 
        
        place_combo = ctk.CTkComboBox(
            self.main_frame,
            values=places,
            variable=self.place_var,
            state="readonly",
            width=300,
            height=45,
            dropdown_fg_color="white",
            dropdown_text_color="black",
            fg_color="#4B7EBF",
            text_color="white",
            corner_radius=6,
            justify="right",
            font=("Arial", 14, "bold")
        )
        place_combo.pack(side="right", padx=10, pady=5)

        # زر البحث
        ctk.CTkButton(
            self.main_frame,
            text="بحث", 
            font=("cairo", 14, "bold"), 
            command=self.search_place_schedule,
            fg_color="#4B7EBF",
            hover_color="#32527B",
            border_width=0,
            corner_radius=6,
            text_color="white",
            height=45,
            width=200
        ).pack(side="right", padx=10, pady=5)

        if not self.table_frames['place']:
            self.table_frames['place'] = tk.Frame(self.results_container, bg=MAIN_PAGE_BUTTONS_FRAME_COLOR)
        for key in self.table_frames:
            if key != 'place' and self.table_frames[key] is not None:
                self.table_frames[key].pack_forget()
        self.table_frames['place'].pack(fill="both", expand=True)
        place_combo.bind("<<ComboboxSelected>>", lambda e: self.search_place_schedule())

    def get_places_from_db(self):
        try:
            db = Database()
            query = "SELECT Location_name FROM Location ORDER BY Location_name"
            db.cursor.execute(query)
            places = [row[0] for row in db.cursor.fetchall()]
            return places if places else ["لا توجد أماكن متاحة"]
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ في جلب الأماكن: {str(e)}")
            return ["خطأ في جلب البيانات"]
        finally:
            db.connection.close()

    def get_level_id(self, level_name):
        levels = {
            "المستوي الأول": 1,
            "المستوي الثاني": 2,
            "المستوي الثالث": 3,
            "المستوي الرابع": 4
        }
        return levels.get(level_name)
    
    def get_departments_from_db(self):
        try:
            db = Database()
            query = "SELECT Department_name FROM Department ORDER BY Department_name"
            db.cursor.execute(query)
            departments = [row[0].strip() for row in db.cursor.fetchall()]  # استخدام strip() لإزالة أي مسافات زائدة
            return departments if departments else ["لا يوجد أقسام"]
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ في جلب الأقسام: {str(e)}")
            return ["خطأ في جلب البيانات"]
        finally:
            db.connection.close()

    def format_schedule_data(self, db_data):
        formatted = {}
        days_order = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
        
        for day in days_order:
            formatted[day] = []
        
        for row in db_data:
            day, start_time, end_time, subject, place, instructor, group_type = row
            formatted[day].append({
                'start': start_time,
                'end': end_time,
                'place': place,
                'group': {
                    'subject': subject,
                    'instructor': instructor,
                    'Group_Type': group_type.lower()
                }
            })
        
        return formatted

    def get_department_id(self, department_name):
        try:
            db = Database()
            query = "SELECT Department_ID FROM Department WHERE Department_name = ?"
            db.cursor.execute(query, (department_name.strip(),))  # استخدام strip() للتأكد من عدم وجود مسافات زائدة
            result = db.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ في البحث عن القسم: {str(e)}")
            return None
        finally:
            db.connection.close()

    def search_schedule(self):
        department = self.department_var.get().strip()
        year = self.year_var.get().strip()

        if year == "المستوي" or department == "القسم":
            messagebox.showwarning("خطأ", "يرجى اختيار جميع الخيارات قبل البحث")
            return
        
        department_id = self.get_department_id(department)
        level_id = self.get_level_id(year)
        
        if department_id is None:
            messagebox.showwarning("خطأ", f"لا يمكن العثور على القسم: {department}")
            return
            
        if level_id is None:
            messagebox.showwarning("خطأ", f"المستوى المحدد غير صالح: {year}")
            return
            
        current_frame = self.table_frames['study']
        for widget in current_frame.winfo_children():
            widget.destroy()
            
        try:
            db = Database()
            schedule_data = db.get_study_schedule(department_id, level_id)
            
            self.update_result_title(f"جدول {department} - {year}")

            if schedule_data:
                # تحويل البيانات إلى التنسيق المطلوب
                formatted_data = self.format_schedule_data(schedule_data)
                self.create_real_schedule_table(current_frame, formatted_data)
            else:
                messagebox.showinfo("لا توجد بيانات", "لا يوجد جدول لهذا القسم والسنة")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ في جلب البيانات: {str(e)}")
            
        self.reset_dropdowns()

    def search_place_schedule(self):
        place = self.place_var.get().strip()
        if place == "اختر المكان" or not place:
            messagebox.showwarning("خطأ", "يرجى اختيار مكان من القائمة")
            return
        
        self.update_result_title(f"جدول المكان: {place}")
        current_frame = self.table_frames['place']
        for widget in current_frame.winfo_children():
            widget.destroy()
            
        try:
            db = Database()
            query = """
            SELECT 
                s.day, 
                s.start_time, 
                s.end_time,
                c.Course_name AS subject,
                loc.Location_name AS place,
                STRING_AGG(d.Department_name, ' + ') AS departments,
                l.F_name + ' ' + l.L_name AS instructor,
                g.Group_Type,
                lvl.Levels_name AS level
            FROM Schedule s
            JOIN Groups g ON s.Group_ID = g.Group_ID
            JOIN Courses c ON g.Course_ID = c.Course_ID
            JOIN Lecturer l ON g.Lecturer_ID = l.Lecturer_ID
            JOIN Location loc ON s.Location_ID = loc.Location_ID
            JOIN Department d ON s.Department_ID = d.Department_ID
            JOIN Levels lvl ON g.Levels_ID = lvl.Levels_ID
            WHERE loc.Location_name = ?
            GROUP BY s.day, s.start_time, s.end_time, c.Course_name, 
                    loc.Location_name, l.F_name, l.L_name, g.Group_Type, lvl.Levels_name
            ORDER BY s.day, s.start_time
            """
            db.cursor.execute(query, (place,))
            schedule_data = db.cursor.fetchall()
            
            if schedule_data:
                formatted_data = self.format_place_schedule_data(schedule_data)
                self.create_real_schedule_table(current_frame, formatted_data, is_place_search=True)
            else:
                messagebox.showinfo("لا توجد بيانات", f"لا يوجد جدول للمكان {place}")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ في جلب البيانات: {str(e)}")
        finally:
            db.connection.close()

    def format_place_schedule_data(self, db_data):
        formatted = {}
        days_order = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
        
        for day in days_order:
            formatted[day] = []
        
        for row in db_data:
            day, start_time, end_time, subject, place, departments, instructor, group_type, level = row
            formatted[day].append({
                'start': start_time,
                'end': end_time,
                'place': place,
                'group': {
                    'subject': subject,
                    'departments': departments,
                    'instructor': instructor,
                    'Group_Type': group_type.lower(),
                    'level': level
                }
            })
        
        return formatted

    def search_teacher_schedule(self):
        teacher_selection = self.teacher_var.get().strip()
        if teacher_selection == "اختر المحاضر" or not teacher_selection:
            messagebox.showwarning("خطأ", "يرجى اختيار محاضر من القائمة")
            return
        
        try:
            teacher_name = teacher_selection.split("(ID:")[0].strip()
            teacher_id = int(teacher_selection.split("(ID:")[1].replace(")", ""))
        except:
            messagebox.showerror("خطأ", "لا يمكن تحديد المحاضر")
            return
        
        self.update_result_title(f"جدول المحاضر: {teacher_name}")
        
        current_frame = self.table_frames['teacher']
        for widget in current_frame.winfo_children():
            widget.destroy()
            
        try:
            db = Database()
            query = """
            SELECT 
                s.day, 
                s.start_time, 
                s.end_time,
                c.Course_name AS subject,
                loc.Location_name AS place,
                STRING_AGG(d.Department_name, ' + ') AS departments,
                lvl.Levels_name AS level,
                g.Group_Type
            FROM Schedule s
            JOIN Groups g ON s.Group_ID = g.Group_ID
            JOIN Courses c ON g.Course_ID = c.Course_ID
            JOIN Lecturer l ON g.Lecturer_ID = l.Lecturer_ID
            JOIN Location loc ON s.Location_ID = loc.Location_ID
            JOIN Department d ON s.Department_ID = d.Department_ID
            JOIN Levels lvl ON g.Levels_ID = lvl.Levels_ID
            WHERE l.Lecturer_ID = ?
            GROUP BY s.day, s.start_time, s.end_time, c.Course_name, 
                    loc.Location_name, lvl.Levels_name, g.Group_Type
            ORDER BY s.day, s.start_time
            """
            db.cursor.execute(query, (teacher_id,))
            schedule_data = db.cursor.fetchall()
            
            if schedule_data:
                formatted_data = self.format_teacher_schedule_data(schedule_data)
                self.create_real_schedule_table(current_frame, formatted_data, is_teacher_search=True)
            else:
                messagebox.showinfo("لا توجد بيانات", "لا يوجد جدول لهذا المحاضر")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ في جلب البيانات: {str(e)}")
        finally:
            db.connection.close()

    def create_real_schedule_table(self, parent, schedule_data, is_place_search=False, is_teacher_search=False):
        table_frame = tk.Frame(parent, bg="#edede9")
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        times = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        total_columns = len(times) - 1  # 11 عمودًا زمنيًا
        days = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]

        # Table Header (day - time)
        tk.Label(
            table_frame, 
            text="اليوم / الوقت", 
            bg="light gray", 
            relief="solid", 
            width=12, 
            anchor='center'
        ).grid(row=0, column=total_columns, sticky="nsew")  # العمود الأخير لعنوان الأيام

        for idx, time_idx in enumerate(range(len(times)-1)):
            col = 10 - idx
            time_str = f"{times[time_idx+1]}:00 - {times[time_idx]}:00"
            tk.Label(
                table_frame, 
                text=time_str, 
                bg='#d3d3d3', 
                relief="groove"
            ).grid(row=0, column=col, sticky="nsew")

        for row_idx, day in enumerate(days, 1):
            # day
            tk.Label(
                table_frame, 
                text=day, 
                bg=TABLE_HEADER_COLOR, 
                relief="groove", 
                width=12, 
                anchor='center'
            ).grid(row=row_idx, column=total_columns, sticky="nsew")  # العمود الأخير
            
            # embty time cell
            for col in range(total_columns):
                tk.Label(table_frame, bg="white", relief="solid").grid(
                    row=row_idx, 
                    column=col, 
                    sticky="nsew"
                )
        
        # fill table w data
        for row_idx, day in enumerate(days, 1):
            if day in schedule_data:
                if is_place_search:
                    for appt in schedule_data[day]:
                        try:
                            start_idx = times.index(appt['start'])
                            end_idx = times.index(appt['end'])
                            col_span = end_idx - start_idx
                            start_col = start_idx
                            
                            group = appt['group']
                            text = f"{group['subject']}\n{group['departments']} - {group['level']}\n{group['instructor']}"
                            bg_color = "#d4edda" if group['Group_Type'] == 'lecture' else "#d4e6f1"
                            
                            if group['Group_Type'] == 'practical':
                                text = f"(عملي)\n{text}"
                            
                            tk.Label(
                                table_frame, 
                                text=text, 
                                bg=bg_color, 
                                font=('Tahoma', 10),
                                relief="solid"
                            ).grid(
                                row=row_idx, 
                                column=start_col, 
                                columnspan=col_span, 
                                sticky="nsew"
                            )
                        except ValueError:
                            continue
                elif is_teacher_search:
                    for row_idx, day in enumerate(days, 1):
                            if day in schedule_data:
                                for appt in schedule_data[day]:
                                    try:
                                        start_idx = times.index(appt['start'])
                                        end_idx = times.index(appt['end'])
                                        col_span = end_idx - start_idx
                                        start_col = start_idx
                                        
                                        group = appt['group']
                                        # عرض جميع الأقسام المشاركة في المحاضرة
                                        text = f"{group['subject']}\n{group['departments']} - {group['level']}\n{appt['place']}"
                                        bg_color = "#d4edda" if group['Group_Type'] == 'lecture' else "#d4e6f1"
                                        
                                        if group['Group_Type'] == 'practical':
                                            text = f"(عملي)\n{text}"
                                        
                                        tk.Label(
                                            table_frame, 
                                            text=text, 
                                            bg=bg_color, 
                                            font=('Tahoma', 10),
                                            relief="solid"
                                        ).grid(
                                            row=row_idx, 
                                            column=start_col, 
                                            columnspan=col_span, 
                                            sticky="nsew"
                                        )
                                    except ValueError:
                                        continue
                else:
                    for appt in schedule_data[day]:
                        try:
                            start_idx = times.index(appt['start'])
                            end_idx = times.index(appt['end'])
                            col_span = end_idx - start_idx
                            # العمود يبدأ من start_idx مباشرة
                            start_col = start_idx
                            
                            group = appt['group']
                            text = f"{group['subject']}\n{group['instructor']}\n{appt['place']}"
                            bg_color = "#d4edda" if group['Group_Type'] == 'lecture' else "#d4e6f1"
                            
                            if group['Group_Type'] == 'practical':
                                text = f"(عملي)\n{text}"
                            
                            tk.Label(
                                table_frame, 
                                text=text, 
                                bg=bg_color, 
                                font=('Tahoma', 10),
                                relief="solid"
                            ).grid(
                                row=row_idx, 
                                column=start_col, 
                                columnspan=col_span, 
                                sticky="nsew"
                            )
                        except ValueError:
                            continue

        for col in range(total_columns + 1):
            table_frame.grid_columnconfigure(col, weight=1)
        for row in range(len(days) + 1):
            table_frame.grid_rowconfigure(row, weight=1)


    # def print_schedule(self):
    #     try:

    #         from datetime import datetime

    #         # تأخير لضمان ظهور الجدول
    #         self.update()
    #         self.update_idletasks()

    #         # تحديد إحداثيات الجدول
    #         x = self.winfo_rootx() + self.results_container.winfo_x()
    #         y = self.winfo_rooty() + self.results_container.winfo_y()
    #         width = self.results_container.winfo_width()
    #         height = self.results_container.winfo_height()

    #         # التقاط صورة للجدول
    #         img = ImageGrab.grab(bbox=(x, y, x + width*1.25, y + height*1.5))

    #         # حفظ الصورة مؤقتًا
    #         temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    #         img.save(temp_img.name, quality=100)

    #         # إنشاء PDF من الصورة
    #         from fpdf import FPDF
    #         pdf = FPDF(orientation='L' if width > height else 'P')
    #         pdf.add_page()
    #         pdf.image(temp_img.name, x=5, y=10, w=pdf.w - 20)  # ضبط الهوامش

    #         # حفظ الملف
    #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #         pdf_file = f"جدول_{timestamp}.pdf"
    #         pdf.output(pdf_file)

    #         # فتح الملف
    #         os.startfile(pdf_file)

    #         # حذف الملف المؤقت
    #         temp_img.close()
    #         os.unlink(temp_img.name)

    #     except Exception as e:
    #         messagebox.showerror("خطأ", f"حدث خطأ أثناء الطباعة: {str(e)}")
    def print_schedule(self):
        if not self.current_mode or not self.table_frames[self.current_mode].winfo_children():
            messagebox.showwarning("تحذير", "لا يوجد جدول معروض للطباعة")
            return
        
        try:
            temp_file = "temp_schedule.pdf"
            
            table_frame = self.table_frames[self.current_mode]
            
            x = table_frame.winfo_rootx()
            y = table_frame.winfo_rooty()
            width = table_frame.winfo_width()
            height = table_frame.winfo_height()
            
            if width <= 0 or height <= 0:
                messagebox.showerror("خطأ", "لا يمكن تحديد حجم الجدول")
                return
                
            img = ImageGrab.grab(bbox=(x, y, x+width*1.25, y+height*1.5))
            img_path = "temp_table.png"
            img.save(img_path)
            
            from fpdf import FPDF
            pdf = FPDF(orientation='L')  # وضع أفقي للصفحة
            pdf.add_page()
            
            pdf.image(img_path, x=10, y=10, w=pdf.w - 20)  # مع هوامش 10 ملم
            
            pdf.output(temp_file)
            
            os.startfile(temp_file)
            
            self.after(1000, lambda: os.remove(img_path))
            
        except ImportError:
            messagebox.showerror("خطأ", "المكتبات المطلوبة غير مثبتة. قم بتثبيت:\n"
                                "pip install pillow fpdf")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الطباعة: {str(e)}")
            
    def create_pdf_from_table(self, table_frame, output_file):
        from fpdf import FPDF
        
        try:
            x = table_frame.winfo_rootx()
            y = table_frame.winfo_rooty()
            width = table_frame.winfo_width()
            height = table_frame.winfo_height()
            
            if width <= 0 or height <= 0:
                raise ValueError("أبعاد الجدول غير صالحة")
                
            img = ImageGrab.grab(bbox=(x, y, x+width* 1.25, y+height*1.5))
            img_path = "temp_table.png"
            img.save(img_path)
            
            pdf = FPDF(orientation='L') 
            pdf.add_page()
            
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, self.current_search_result, 0, 1, 'C')
            pdf.ln(10)
            
            pdf.image(img_path, x=10, y=30, w=270)  # ضبط الأبعاد حسب الحاجة
            
            pdf.output(output_file)
            
            os.remove(img_path)
            
        except ImportError:
            messagebox.showerror("خطأ", "المكتبات المطلوبة غير مثبتة. قم بتثبيت:\n"
                                "pip install fpdf pillow")
class MainPage:
    """Main application class that manages all pages"""
    def __init__(self, master=None):
        self.main = tk.Tk() if master is None else tk.Toplevel(master)
        self.main.geometry("900x600")
        self.main.minsize(900, 700)
        self.main.resizable(True, True)
        self.main.title("برنامج إدارة الجداول الدراسية")
        self.main.iconbitmap("damiettaIcon.ico")
        
        
        # Initialize Data Manager
        self.data_manager = DataManager()
        
        self.load_config()
        
        # Initialize pages
        self.main_frame = tk.Frame(self.main)
        self.schedule_entry_page = None
        self.data_entry_page = None
        self.study_tables_page = StudyTablesPage(self.main, self.show_main_page)
        self.schedule_placer_page = None
        
        self.setup_main_page()
        self.main_frame.pack(expand=True, fill="both")
   
    def load_config(self):
        """تحميل إعدادات الاتصال من ملف config.ini"""
        self.config = configparser.ConfigParser()
        try:
            self.config.read('config.ini')
            self.db_server = self.config.get('DATABASE', 'SERVER', fallback='.')
            self.db_name = self.config.get('DATABASE', 'DATABASE', fallback='project')
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل ملف الإعدادات: {str(e)}")
            self.db_server = '.'
            self.db_name = 'project'
        
        
        
    def setup_main_page(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Main.TButton", 
                        font=("Arial", 12, "bold"),
                        foreground="black",
                        background="white",
                        borderwidth=2,
                        padding=5,
                        relief="raised")
        style.map("Main.TButton",
                  background=[("active", MAIN_PAGE_BUTTONS_HOVER), ("!disabled", "white")], 
                  foreground=[("active", "white")])
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.style = ttk.Style()
        self.style.configure("Header.TFrame", background=HEADER_FRAME) 
        self.style.configure("Buttons.TFrame", background=MAIN_PAGE_BUTTONS_FRAME_COLOR)
        self.style.configure("Header.TLabel", font=("Traditional Arabic", 36, 'bold'), background=HEADER_FRAME, foreground="white")
        self.style.configure("Main.TButton", font=("Cairo", 16), padding=10)

        self.header_frame = ttk.Frame(self.main_frame, style="Header.TFrame")
        self.header_frame.pack(fill="both")
        self.header_label = ttk.Label(self.header_frame, text="برنامج إدارة الجداول", style="Header.TLabel")
        self.header_label.pack(pady=40)

        self.buttons_frame = ttk.Frame(self.main_frame, style="Buttons.TFrame")
        self.buttons_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.enter_tables = ttk.Button(self.buttons_frame, 
                                     text="إدخال المجموعات", 
                                     style="Main.TButton", 
                                     command=self.show_schedule_entry_page)
        self.enter_tables.pack(pady=10, padx=20, fill="x")
        
        
        # Enter tables page button

        place_schedule_btn = ttk.Button(self.buttons_frame, 
                                            text="إدخال الجداول الدراسية", 
                                            style="Main.TButton", 
                                            command=self.show_schedule_placer_page)
        place_schedule_btn.pack(pady=10, padx=20, fill="x")

        self.view_table_button = ttk.Button(
            self.buttons_frame, 
            text="عرض الجداول الدراسية", 
            style="Main.TButton", 
            command=self.show_study_tables_page
        )
        self.view_table_button.pack(pady=10, padx=20, fill="x")
        
        self.data_entry_button = ttk.Button(
            self.buttons_frame, 
            text="ادارة البيانات", 
            style="Main.TButton", 
            command=self.show_data_entry_page
        )
        self.data_entry_button.pack(pady=10, padx=20, fill="x")
        
        # زرار الاعدادات
        settings_button = ttk.Button(
        self.buttons_frame, 
        text="الإعدادات", 
        style="Main.TButton", 
        command=self.show_settings
        )
        settings_button.pack(pady=10, padx=20, fill="x")
        
    def show_settings(self):
        """عرض نافذة إعدادات الاتصال بقاعدة البيانات"""
        settings_window = tk.Toplevel(self.main)
        settings_window.title("إعدادات الاتصال بقاعدة البيانات")
        settings_window.geometry("400x200")
    
        tk.Label(settings_window, text="اسم السيرفر:").pack(pady=5)
        server_entry = ttk.Entry(settings_window)
        server_entry.insert(0, self.db_server)
        server_entry.pack(fill='x', padx=20)
    
        tk.Label(settings_window, text="اسم قاعدة البيانات:").pack(pady=5)
        db_entry = ttk.Entry(settings_window)
        db_entry.insert(0, self.db_name)
        db_entry.pack(fill='x', padx=20)
        
        
        def save_settings():
            try:
                self.db_server = server_entry.get().strip()
                self.db_name = db_entry.get().strip()

                self.config['DATABASE'] = {
                    'SERVER': self.db_server,
                    'DATABASE': self.db_name
                    }
                with open('config.ini', 'w') as configfile:
                    self.config.write(configfile)

                messagebox.showinfo("تم الحفظ", "تم حفظ الإعدادات بنجاح")
                settings_window.destroy()
            except Exception as e:
                messagebox.showerror("خطأ أثناء الحفظ", f"حدث خطأ: {str(e)}")

        ttk.Button(settings_window, text="حفظ", command=save_settings).pack(pady=10)
     
    def show_schedule_entry_page(self):
        """Show the schedule entry page"""
        self.main_frame.pack_forget()
        if self.schedule_entry_page is None:
            self.schedule_entry_page = GroupsCreation(self.main, self.show_main_page)
            # ربط بيانات الصفحة بمدير البيانات
            self.schedule_entry_page.groups = self.data_manager.groups_data
            self.schedule_entry_page.data_manager = self.data_manager
        self.schedule_entry_page.pack(fill=tk.BOTH, expand=True)
        self.main.geometry("900x600")
        self.main.title("نظام إدخال الجداول")

    def show_data_entry_page(self):
        """Show the data entry page"""
        self.main_frame.pack_forget()
        if self.data_entry_page is None:
            self.data_entry_page = DataEntryPage(self.main, self.show_main_page)
        self.data_entry_page.pack(fill=tk.BOTH, expand=True)
        self.main.geometry("900x600")
        self.main.title("نظام إدخال البيانات")

    def show_study_tables_page(self):
        """Show the study tables page"""
        self.main_frame.pack_forget()
        self.study_tables_page.pack(expand=True, fill="both")
        self.main.geometry("900x600")
        self.main.title("عرض الجداول الدراسية")

    
    def show_main_page(self):
        """Return to the main page"""
        if self.schedule_entry_page:
            self.schedule_entry_page.pack_forget()
        if self.data_entry_page:
            self.data_entry_page.pack_forget()
        if self.study_tables_page:
            self.study_tables_page.pack_forget()
        if self.schedule_placer_page:
            self.schedule_placer_page.pack_forget()
            
        self.main_frame.pack(expand=True, fill="both")
        self.main.geometry("900x600")
        self.main.title("برنامج إدارة الجداول الدراسية")


    def show_schedule_placer_page(self):
        """عرض صفحة وضع الجداول"""
        self.main_frame.pack_forget()
        
        groups_data = self.data_manager.groups_data 
        
        self.schedule_placer_page = SchedulePlacerPage(
            self.main, 
            self.show_main_page, 
            groups_data
        )
        self.schedule_placer_page.data_manager = self.data_manager
        self.schedule_placer_page.schedule_data = self.data_manager.schedule_data
        
        self.schedule_placer_page.pack(fill=tk.BOTH, expand=True)
        self.main.geometry("900x600")
        self.main.title("وضع الجداول الدراسية")
        
    def run(self):
        self.main.mainloop()

if __name__ == "__main__":
    app = MainPage()
    app.run()
