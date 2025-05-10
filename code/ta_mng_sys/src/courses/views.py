from django.shortcuts import render
from .forms import UploadExcelForm
import openpyxl
from django.http import HttpResponse


def upload_student_excell(request):
    data = []
    classrooms = []
    assigned_classrooms = {}
    error = None

    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = form.cleaned_data['excel_file']
            classrooms = form.cleaned_data['classroom_selection']  # This is a queryset

            if not excel_file.name.endswith('.xlsx'):
                error = "Please upload a valid .xlsx file."
            else:
                try:
                    wb = openpyxl.load_workbook(excel_file)
                    sheet = wb.active

                    for row in sheet.iter_rows(min_row=2, values_only=True):
                        name, surname, student_id = row
                        data.append({
                            'name': name,
                            'surname': surname,
                            'id': student_id
                        })

                    data.sort(key=lambda x: x['surname'])

                    assigned_classrooms = {cls: [] for cls in classrooms}
                    num_classrooms = len(classrooms)
                    students_per_classroom = len(data) // num_classrooms
                    remainder = len(data) % num_classrooms

                    start = 0
                    for i, classroom in enumerate(classrooms):
                        extra = 1 if i < remainder else 0  # Distribute remaining students fairly
                        end = start + students_per_classroom + extra
                        assigned_classrooms[classroom] = data[start:end]
                        start = end
                    
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "Student Assignments"

                    row_num = 1
                    for classroom, student_list in assigned_classrooms.items():
                        ws.cell(row=row_num, column=1, value=f"Classroom: {classroom}")
                        row_num += 1
                        ws.cell(row=row_num, column=1, value="Name")
                        ws.cell(row=row_num, column=2, value="Surname")
                        ws.cell(row=row_num, column=3, value="ID")
                        row_num += 1

                        for student in student_list:
                            ws.cell(row=row_num, column=1, value=student['name'])
                            ws.cell(row=row_num, column=2, value=student['surname'])
                            ws.cell(row=row_num, column=3, value=student['id'])
                            row_num += 1

                        row_num += 2  # space between classrooms

                    # Prepare response
                    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = 'attachment; filename=assigned_students.xlsx'

                    # Save workbook to response
                    wb.save(response)
                    return response

                except Exception as e:
                    error = f"Failed to read Excel file: {str(e)}"
    else:
        form = UploadExcelForm()

    return render(request, 'courses/upload_student_excell.html', {
        'form': form,
        'data': data,
        'classrooms': classrooms,
        'assigned_classrooms': assigned_classrooms,
        'error': error
    })