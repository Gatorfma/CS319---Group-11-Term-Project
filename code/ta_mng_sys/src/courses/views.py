from django.contrib import messages  # ✔️ bu olacak

import pandas as pd
from django.shortcuts import redirect, render

from courses.models import Course, CourseOffering

from accounts.models import CustomUser, InstructorProfile, Student, TAProfile

# Create your views here.
def import_data_view(request):
    

    def parse_semester(semester_code):
        year = int(str(semester_code)[:4])
        season_code = str(semester_code)[-1]
        season_map = {'1': 'Fall', '2': 'Spring', '3': 'Summer'}
        season = season_map.get(season_code, 'Fall')
        return f"{season} {year}"

    if request.method == 'POST':
        import_type = request.POST.get("import_type")
        file_key = f"{import_type}_file"
        uploaded_file = request.FILES.get(file_key)

        if not uploaded_file:
            messages.error(request, "No file selected.")
            return redirect('courses:import_data')

        try:
            df = pd.read_excel(uploaded_file)

            if import_type == "courses":
                df = df.rename(columns={
                    'department_code': 'department_code',
                    'course_no': 'course_code',
                    'course_name': 'title'
                })

                for _, row in df.iterrows():
                    department_code = row['department_code'].strip().upper()
                    course_code = int(row['course_code'])
                    title = row['title'].strip()

                    Course.objects.get_or_create(
                        department_code=department_code,
                        course_code=course_code,
                        defaults={'title': title}
                    )

            elif import_type == "faculty":
                df = df.rename(columns={'department_code': 'department'})
                for _, row in df.iterrows():
                    department = row['department'].strip().upper()
                    staff_id = str(int(row['staff_id']))
                    first_name = row['first_name'].strip()
                    last_name = row['last_name'].strip()
                    email = row['email'].strip()

                    user, created = CustomUser.objects.get_or_create(
                        employee_id=staff_id,
                        defaults={
                            'username': f"instructor{staff_id}",
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email,
                            'role': CustomUser.Roles.INSTRUCTOR,
                            'department': department
                        }
                    )

                    if created:
                        user.set_password("defaultpass123")
                    else:
                        user.first_name = first_name
                        user.last_name = last_name
                        user.email = email
                        user.role = CustomUser.Roles.INSTRUCTOR
                        user.department = department

                    user.save()

                    if not hasattr(user, 'instructor_profile'):
                        InstructorProfile.objects.create(
                            user=user,
                            is_faculty=bool(row.get('is_faculty', True)),
                            is_active=bool(row.get('is_active', True))
                        )
                    else:
                        profile = user.instructor_profile
                        profile.is_faculty = bool(row.get('is_faculty', True))
                        profile.is_active = bool(row.get('is_active', True))
                        profile.save()

            elif import_type == "students":
                df = df.rename(columns={'department_code': 'department', 'class': 'student_class'})
                for _, row in df.iterrows():
                    student_id = str(row['student_id']).strip()
                    first_name = row['first_name'].strip()
                    last_name = row['last_name'].strip()

                    student, created = Student.objects.get_or_create(
                        student_id=student_id,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name
                        }
                    )

                    if not created:
                        if student.first_name != first_name or student.last_name != last_name:
                            student.first_name = first_name
                            student.last_name = last_name
                            student.save()

                    if str(row.get('is_ta', '')).strip() == '1':
                        department = row['department'].strip().upper()
                        email = row['email'].strip()
                        student_class = int(row['student_class'])

                        ta_type = 'PHD' if student_class == 9 else 'GRAD'

                        user, created = CustomUser.objects.get_or_create(
                            username=student_id,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email,
                                'role': CustomUser.Roles.TA,
                                'department': department
                            }
                        )

                        if created:
                            user.set_password("defaultpass123")
                        else:
                            user.first_name = first_name
                            user.last_name = last_name
                            user.email = email
                            user.department = department
                            user.role = CustomUser.Roles.TA

                        user.employee_id = student_id
                        user.phone_number = row.get('phone_no', '').strip()
                        user.save()

                        if not hasattr(user, 'ta_profile'):
                            TAProfile.objects.create(
                                user=user,
                                ta_type=ta_type,
                                is_active=bool(row.get('is_active', True)),
                                proctor_type=int(row['proctor_type']) if pd.notna(row.get('proctor_type')) else 0,
                                
                            )
                        else:
                            profile = user.ta_profile
                            profile.ta_type = ta_type
                            profile.is_active = bool(row.get('is_active', True))
                            profile.proctor_type = int(row['proctor_type']) if pd.notna(row.get('proctor_type')) else 0
                            profile.save()

            elif import_type == "course_offerings":
                df = df.rename(columns={'department_code': 'department'})
                for _, row in df.iterrows():
                    department = row['department'].strip().upper()
                    course = Course.objects.filter(department_code=department, course_code=int(row['course_no'])).first()
                    if not course:
                        messages.warning(request, f"Course not found: {department}{row['course_no']}")
                        continue
                    semester = parse_semester(row['semester'])
                    section = int(row['section_no'])
                    staff_id = str(int(row['staff_id']))
                    user, _ = CustomUser.objects.get_or_create(
                        employee_id=staff_id,
                        defaults={
                            'username': f"instructor{staff_id}",
                            'first_name': 'Auto',
                            'last_name': 'Generated',
                            'role': CustomUser.Roles.INSTRUCTOR,
                            'department': department
                        }
                    )
                    user.set_password("defaultpass123")
                    user.save()
                    
                    offering, _ = CourseOffering.objects.get_or_create(
                        course=course,
                        semester=semester,
                        section=section,
                        defaults={
                            'max_capacity': 100,  
                            'enrolled_count': 0,
                            
                            
                        } 
                    )
                    offering.instructors.add(user)
                    if not hasattr(user, 'instructor_profile'):
                        InstructorProfile.objects.create(user=user)

                    # Bu kısım her durumda çalışmalı, o yüzden dışarıda tutulmalı
                    if hasattr(user, 'instructor_profile'):
                        user.instructor_profile.assigned_course_offerings.add(offering)


            elif import_type == "enrollments":
                df = df.rename(columns={'department_code': 'department'})
                for _, row in df.iterrows():
                    department = row['department'].strip().upper()
                    student_id = str(row['student_id']).strip()
                    semester = parse_semester(row['semester'])
                    section = int(row['section_no'])
                    course = Course.objects.filter(department_code=department, course_code=int(row['course_no'])).first()
                    if not course:
                        messages.warning(request, f"Course not found: {department}{row['course_no']}")
                        continue
                    offering = CourseOffering.objects.filter(course=course, semester=semester, section=section).first()
                    if not offering:
                        messages.warning(request, f"Offering not found for {course} - {semester} Sec {section}")
                        continue
                    student = Student.objects.filter(student_id=student_id).first()
                    if not student:
                        messages.warning(request, f"Student not found: {student_id}")
                        continue
                    offering.students.add(student)
                    student.enrolled_courses.add(offering)
                    offering.enrolled_count = offering.students.count()
                    offering.save()

                    try:
                        user = CustomUser.objects.get(username=student_id)
                        if hasattr(user, 'ta_profile'):
                            user.ta_profile.enrolled_course_offerings.add(offering)
                    except CustomUser.DoesNotExist:
                        pass

            messages.success(request, f"{import_type.replace('_', ' ').title()} imported successfully.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"Import failed: {e}")

        return redirect('courses:import_data')


    import_types = [
    ("courses", "Courses"),
    ("faculty", "Faculty"),
    ("students", "Students"),
    ("course_offerings", "Course Offerings"),
    ("enrollments", "Enrollments"),
    ]
    return render(request, 'courses/import_data.html', {"import_types": import_types})
