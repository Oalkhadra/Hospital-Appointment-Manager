import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

from hospital_db import Department, Appointment, Reception, Practitioner, Patient, PatientOf, Base, hash_department, engine_urls  # Import your Appointment class and Base from your module

# User credentials
users = {
    "omar": {
        "username": "omar",
        "password": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt())
    },
    "tomine": {
        "username": "tomine",
        "password": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt())
    }
}


# Define a custom session state class
class SessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

# Create a session state object
session_state = SessionState(logged_in=False)


# Define Login Page
def login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True
    
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and bcrypt.checkpw(password.encode('utf-8'), users[username]["password"]):
            st.session_state.logged_in = True
            st.success("Logged in as {}".format(username))
            return True
        else:
            st.error("Invalid credentials")
    return False


# Define Home Page
def home_page():
    st.title("Appointment Management System")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Appointments", "Patients", "Patient Of", "Practitioners", "Receptionists", "Departments"])
    
    # Appointments Tab
    with tab1:
        st.title('Appointments')
        subtab1, subtab2, subtab3, subtab4 = st.tabs(["New Appointments", "Appointment Information", "Modify Appointments", "Delete Appointments"])

        # Adding Appointments
        with subtab1:
            filter_options = {
                "DepartmentID": st.number_input("Department ID",  value= None, step=1, key="Add Department ID, appointments"),
                "ReceptionistID": st.number_input("Receptionist ID", value= None, step=1, key="Add Receptionist ID, appointments"),
                "PatientID": st.number_input("Patient ID", value=None, step=1, key="Add Patient ID, appointments"),
                "PractitionerID": st.number_input("Practitioner ID",  value= None, step=1, key="Add Practitioner ID, appointments"),
                "AppointmentDate": st.date_input("Appointment Date", value = None, key="Add Appointment Date, appointments"),
                "AppointmentTime": st.time_input("Appointment Time", value = None, key="Add Appointment Time, appointments"),
                "Notes": st.text_area("Notes", value = 'None', key="Add Notes, appointments")
            }

            if st.button('Add Appointment'):
                db_num = hash_department(filter_options["DepartmentID"])
                engine1 = create_engine(engine_urls[db_num])
                
                # create session class
                Session1 = sessionmaker(bind=engine1)
                session1 = Session1()  # session instance

                filtering_dict = {key: value for key, value in filter_options.items() if value}
                new_appointment = Appointment.add_appointment(session1, filtering_dict)

                if new_appointment:
                    st.success(f'Appointment added successfully.')
                
                else:
                    st.error(f'Appointment not added, please ensure all information is correct.')

        # Retrieve Appointment Information
        with subtab2:
            filter_options = {
                "AppointmentID": st.number_input("Appointment ID", value= None, step=1, key="Get Appointment ID, appointments"),
                "PatientID": st.number_input("Patient ID", value=None, step=1, key="Get Patient ID, appointments"),
                "DepartmentID": st.number_input("Department ID",  value= None, step=1, key="Get Department ID, appointments"),
                "ReceptionistID": st.number_input("Receptionist ID", value= None, step=1, key="Get Receptionist ID, appointments"),
                "PractitionerID": st.number_input("Practitioner ID",  value= None, step=1, key="Get Practitioner ID, appointments"),
                "AppointmentDate": st.date_input("Appointment Date", value = None, key="Get Appointment Date, appointments"),
                "AppointmentTime": st.time_input("Appointment Time", value = None, key="Get Appointment Time, appointments"),
                "Notes": st.text_area("Notes", value = None, key="Get Notes, appointments")
            }
            
            if st.button("Retrieve Appointment Information"):
                # create session class
                engine1 = create_engine(engine_urls[1])
                Session1 = sessionmaker(bind=engine1)
                session1 = Session1()  # session instance
               
                engine2 = create_engine(engine_urls[0])
                Session2 = sessionmaker(bind=engine2)
                session2 = Session2()  # session instance

                filtering_dict = {key: value for key, value in filter_options.items() if value}
                appointments, tot_count = Appointment.get_appointment(session1, session2, filtering_dict)

                if appointments:
                    st.subheader(f"{tot_count} Appointment(s) found:")
                    for i in range(len(appointments)):
                        st.write(f"Appointment ID: {appointments[i].AppointmentID}")
                        st.write(f"Department ID: {appointments[i].DepartmentID}")
                        st.write(f"Receptionist ID: {appointments[i].ReceptionistID}")
                        st.write(f"Patient ID: {appointments[i].PatientID}")
                        st.write(f"Practitioner ID: {appointments[i].PractitionerID}")
                        st.write(f"Appointment Date: {appointments[i].AppointmentDate}")
                        st.write(f"Appointment Time: {appointments[i].AppointmentTime}")
                        st.write(f"Notes: {appointments[i].Notes}")
                        st.write("---")
                else:
                    st.write("No appointments found matching the filtering criteria.")
        
        # Modify Appointment Information
        with subtab3:
            st.subheader("Please input the information of the appointment(s) you would like modify")
            filter_options_tofind = {
                "AppointmentID": st.number_input("Appointment ID", value= None, step=1, key="ModifyGet Appointment ID, appointments"),
                "DepartmentID": st.number_input("Department ID",  value= None, step=1, key="ModifyGet Department ID, appointments"),
                "ReceptionistID": st.number_input("Receptionist ID", value= None, step=1, key="ModifyGet Receptionist ID, appointments"),
                "PatientID": st.number_input("Patient ID", value=None, step=1, key="ModifyGet Patient ID, appointments"),
                "PractitionerID": st.number_input("Practitioner ID",  value= None, step=1, key="ModifyGet Practitioner ID, appointments"),
                "AppointmentDate": st.date_input("Appointment Date", value = None, key="ModifyGet Appointment Date, appointments"),
                "AppointmentTime": st.time_input("Appointment Time", value = None, key="ModifyGet Appointment Time, appointments"),
                "Notes": st.text_area("Notes", value = None, key="ModifyGet Notes, appointments")
            }
            

            st.subheader("Please input the new information for the appointment(s)")
            filter_options_tomodify = {
                "ReceptionistID": st.number_input("Receptionist ID", value= None, step=1, key="Modify Receptionist ID, appointments"),
                "PatientID": st.number_input("Patient ID", value=None, step=1, key="Modify Patient ID, appointments"),
                "PractitionerID": st.number_input("Practitioner ID",  value= None, step=1, key="Modify Practitioner ID, appointments"),
                "AppointmentDate": st.date_input("Appointment Date", value = None, key="Modify Appointment Date, appointments"),
                "AppointmentTime": st.time_input("Appointment Time", value = None, key="Modify Appointment Time, appointments"),
                "Notes": st.text_area("Notes", value = None, key="Modify Notes, appointments")
            }

            if st.button('Modify Appointment(s)'):
                # create session class
                engine1 = create_engine(engine_urls[1])
                Session1 = sessionmaker(bind=engine1)
                session1 = Session1()  # session instance
               
                engine2 = create_engine(engine_urls[0])
                Session2 = sessionmaker(bind=engine2)
                session2 = Session2()  # session instance

                filtering_dict_tofind = {key: value for key, value in filter_options_tofind.items() if value}
                filtering_dict_tomodify = {key: value for key, value in filter_options_tomodify.items() if value}

                modifiedAppointment = Appointment.modify_appointment(session1, session2, filtering_dict_tofind, filtering_dict_tomodify) 
                
                if modifiedAppointment:
                    st.success(f'Appointment modified successfully.')
                
                else:
                    st.error(f'Appointment was not modified, please ensure all information is correct.')

        # Delete Appointment
        with subtab4:
            filter_options = {
                "AppointmentID": st.number_input("Appointment ID", value= None, step=1, key="Delete Appointment, appointments")
            }

            if st.button('Delete Appointment'):
                engine1 = create_engine(engine_urls[1])
                Session1 = sessionmaker(bind=engine1)
                session1 = Session1()  # session instance
               
                engine2 = create_engine(engine_urls[0])
                Session2 = sessionmaker(bind=engine2)
                session2 = Session2()  # session instance
                
                filtering_dict = {key: value for key, value in filter_options.items() if value}
                Appointment.delete_appointment(session1, session2, filtering_dict)
                
                st.success(f'Appointment successfully deleted')


    # Patients Tab
    with tab2:
        st.title('Patients')
        subtab1, subtab2, subtab3 = st.tabs(["New Patients", "Patient Information", "Modify Patient Information"])

        # Add Patient
        with subtab1:
            filter_options = {
                "PatientID": st.number_input('Patient ID', min_value=1, step=1, key="Add Patient ID, patients"),
                "DepartmentID": st.number_input('Department ID', min_value=1, step=1, key="Add Department ID, patients"),
                "LastName": st.text_input('Last Name', key="Add Last Name, patients"),
                "FirstName": st.text_input('First Name', key="Add First Name, patients"),
                "DOB": st.date_input('Date of Birth', key='Add DOB, patients', ),
                "Gender": st.text_input('Gender', key='Add Gender, patients'),
                "Insurance": st.text_input('Insurance', key="Add Insurance, patients"),
                "PastProcedures": st.text_input('Past Procedures', key="Add Past Procedures, patients"),
                "Notes": st.text_area('Notes', key="Add Notes, patients")
            }

            if st.button('Add Patient'):
                db_num = hash_department(filter_options["DepartmentID"])
            
                # create session class
                engine = create_engine(engine_urls[db_num])
                Session = sessionmaker(bind=engine)
                session = Session()  # session instance
                
                filtering_dict = {key: value for key, value in filter_options.items() if value}

                new_patient = Patient.add_patient(session, filtering_dict)
                
                if new_patient:
                    st.success(f'Patient added successfully. ID: {new_patient.PatientID}')
                
                else:
                    st.error(f'Patient not added, please ensure all necessary information is filled and correct.')
                
        
        # Retrieve Patient Information
        with subtab2:
            filter_options = {
                "PatientID": st.number_input('Patient ID', value=None, step=1, key="Get Patient ID, patients"),
                "DepartmentID": st.number_input('Department ID', value=None, step=1, key="Get Department ID, patients"),
                "LastName": st.text_input('Last Name', value=None, key="Get Last Name, patients"),
                "FirstName": st.text_input('First Name', value=None, key="Get First Name, patients"),
                "DOB": st.date_input('Date of Birth', value=None, key='Get DOB, patients', ),
                "Gender": st.text_input('Gender', value=None, key='Get Gender, patients'),
                "SchedulingState": st.text_input('Scheduling state', value=None, key='Get SS, patients'),
                "Insurance": st.text_input('Insurance', value=None, key="Get Insurance, patients"),
                "PastProcedures": st.text_input('Past Procedures', value=None, key="Get Past Procedures, patients"),
                "Notes": st.text_area('Notes', value=None, key="Get Notes, patients")
            }

            if st.button("Retrieve Patient Information"):
                # create session class
                engine1 = create_engine(engine_urls[1])
                Session1 = sessionmaker(bind=engine1)
                session1 = Session1()  # session instance
               
                engine2 = create_engine(engine_urls[0])
                Session2 = sessionmaker(bind=engine2)
                session2 = Session2()  # session instance

                filtering_dict = {key: value for key, value in filter_options.items() if value}
                patients, tot_count = Patient.get_patient(session1, session2, filtering_dict)

                if patients:
                    st.subheader(f"{tot_count} Patient(s) found:")
                    for i in range(len(patients)):
                        st.write(f"Patient ID: {patients[i].PatientID}")
                        st.write(f"Department ID: {patients[i].DepartmentID}")
                        st.write(f"Last Name: {patients[i].LastName}")
                        st.write(f"First Name: {patients[i].FirstName}")
                        st.write(f"Scheduling State: {patients[i].SchedulingState}")
                        st.write(f"Date of Birth: {patients[i].DOB}")
                        st.write(f"Gender: {patients[i].Gender}")
                        st.write(f"Insurance: {patients[i].Insurance}")
                        st.write(f"Past Procedures: {patients[i].PastProcedures}")
                        st.write(f"Notes: {patients[i].Notes}")
                        st.write("---")
                else:
                    st.write("No patient(s) found matching the filtering criteria.")

        # Modify Patient Information
        with subtab3:
            st.subheader("Please input the information of the patient(s) you would like modify")
            filter_options_tofind = {
                "PatientID": st.number_input('Patient ID', value=None, step=1, key="ModifyGet Patient ID, patients"),
                "DepartmentID": st.number_input('Department ID', value=None, step=1, key="ModifyGet Department ID, patients"),
                "LastName": st.text_input('Last Name', value=None, key="ModifyGet Last Name, patients"),
                "FirstName": st.text_input('First Name', value=None, key="ModifyGet First Name, patients"),
                "DOB": st.date_input('Date of Birth', value=None, key='ModifyGet DOB, patients', ),
                "Gender": st.text_input('Gender', value=None, key='ModifyGet Gender, patients'),
                "SchedulingState": st.text_input('Scheduling state', value=None, key='Modify SS, patients'),
                "Insurance": st.text_input('Insurance', value=None, key="ModifyGet Insurance, patients"),
                "PastProcedures": st.text_input('Past Procedures', value=None, key="ModifyGet Past Procedures, patients"),
                "Notes": st.text_area('Notes', value=None, key="ModifyGet Notes, patients")
            }
            
            st.subheader("Please input the new information for the patient(s)")
            filter_options_tomodify = {
                "PatientID": st.number_input('Patient ID', value=None, step=1, key="Modify Patient ID, patients"),
                "LastName": st.text_input('Last Name', value=None, key="Modify Last Name, patients"),
                "FirstName": st.text_input('First Name', value=None, key="Modify First Name, patients"),
                "DOB": st.date_input('Date of Birth', value=None, key='Modify DOB, patients', ),
                "Gender": st.text_input('Gender', value=None, key='Modify Gender, patients'),
                "Insurance": st.text_input('Insurance Status', value=None, key="Modify Insurance, patients"),
                "PastProcedures": st.text_input('Past Procedures', value=None, key="Modify Past Procedures, patients"),
                "Notes": st.text_area('Notes', value=None, key="Modify Notes, patients")
            }

            if st.button('Modify Patient(s)'):
                # create session class
                engine1 = create_engine(engine_urls[1])
                Session1 = sessionmaker(bind=engine1)
                session1 = Session1()  # session instance
               
                engine2 = create_engine(engine_urls[0])
                Session2 = sessionmaker(bind=engine2)
                session2 = Session2()  # session instance

                filtering_dict_tofind = {key: value for key, value in filter_options_tofind.items() if value}
                filtering_dict_tomodify = {key: value for key, value in filter_options_tomodify.items() if value}

                modifiedPatient = Patient.modify_patient(session1, session2, filtering_dict_tofind, filtering_dict_tomodify) 
                
                if modifiedPatient:
                    st.success(f'Patient(s) modified successfully.')
                
                else:
                    st.error(f'Patient(s) not modified, please ensure all necessary information is filled and correct.')
                
    # Patient_Of Tab
    with tab3:
        subtab1, subtab2 = st.tabs(["Patients by Practitioner", "Practitioners by Patients"])

        # Search by Practitioner
        with subtab1:
            st.title('Patient Of')
            st.subheader("Patient Information per Practitioner")

            practitioner_id_input =  st.number_input("Practitioner ID", value=None, step=1, key="Get Patient For, PatientOf")

            if st.button("Retrieve Patient Of Information"):
                # create session class
                engine1 = create_engine(engine_urls[1])
                Session1 = sessionmaker(bind=engine1)
                session1 = Session1()  # session instance
                
                engine2 = create_engine(engine_urls[0])
                Session2 = sessionmaker(bind=engine2)
                session2 = Session2()  # session instance

                patients, tot_count = PatientOf.get_patients_of(session1, session2, practitioner_id_input)

                if patients:
                    st.subheader(f"{tot_count} Patient(s) found:")
                    for i in range(len(patients)):
                        st.write(f"Patient ID: {patients[i][1][0].PatientID}")
                        st.write(f"Department ID: {patients[i][1][0].DepartmentID}")
                        st.write(f"Last Name: {patients[i][1][0].LastName}")
                        st.write(f"First Name: {patients[i][1][0].FirstName}")
                        st.write(f"Scheduling State: {patients[i][1][0].SchedulingState}")
                        st.write(f"Date of Birth: {patients[i][1][0].DOB}")
                        st.write(f"Gender: {patients[i][1][0].Gender}")
                        st.write(f"Insurance: {patients[i][1][0].Insurance}")
                        st.write(f"Past Procedures: {patients[i][1][0].PastProcedures}")
                        st.write(f"Notes: {patients[i][1][0].Notes}")
                        st.write("---")
                else:
                    st.write("No Patients found matching the filtering criteria.")

        # Search by Patient
        with subtab2:
            st.title('Practitioner For')
            st.subheader("Practitioner Information by Patient")

            patient_id_input =  st.number_input("Patient ID", value=None, step=1, key="Get Practitioner For, PatientOf")

            if st.button("Retrieve Practitioner For Information"):
                # create session class
                engine1 = create_engine(engine_urls[1])
                Session1 = sessionmaker(bind=engine1)
                session1 = Session1()  # session instance
                
                engine2 = create_engine(engine_urls[0])
                Session2 = sessionmaker(bind=engine2)
                session2 = Session2()  # session instance

                practitioners, tot_count = PatientOf.get_practitioners_for(session1, session2, patient_id_input)
                
                if practitioners:
                    st.subheader(f"{tot_count} Practitioner(s) found:")
                    for i in range(len(practitioners)):
                        st.write(f"Practitioner ID: {practitioners[i][1][0].EmployeeID}")
                        st.write(f"Department ID: {practitioners[i][1][0].DepartmentID}")
                        st.write(f"Last Name: {practitioners[i][1][0].LastName}")
                        st.write(f"First Name: {practitioners[i][1][0].FirstName}")
                        st.write(f"Title: {practitioners[i][1][0].Title}")
                        st.write(f"License Number: {practitioners[i][1][0].LicenseNumber}")
                        st.write(f"Specialty: {practitioners[i][1][0].Specialty}")
                        st.write("---")
                else:
                    st.write("No Practitioners found matching the filtering criteria.")

    # Practitioners Tab
    with tab4:
        st.title('Practitioners')
        st.subheader("Practitioner Information")

        filter_options = {
            "EmployeeID": st.number_input("Employee ID", value=None, step=1, key="Get Employee ID, employees"),
            "DepartmentID": st.number_input("Department ID", value=None, step=1, key="Get Department ID, employees"),
            "LastName": st.text_input("Last Name", value=None, key="Get Last Name, employees"),
            "FirstName": st.text_input("First Name", value=None, key="Get First Name, employees"),
            "LicenseNumber": st.number_input("License Number", value=None, step=1, key="Get License Number, employees"),
            "Title": st.text_input("Title", value=None, key="Get Title, employees"),
            "Specialty": st.text_input("Specialty", value=None, key="Get Specialty, employees")
            }

        if st.button("Retrieve Practitioner Information"):
            # create session class
            engine1 = create_engine(engine_urls[1])
            Session1 = sessionmaker(bind=engine1)
            session1 = Session1()  # session instance

            
            engine2 = create_engine(engine_urls[0])
            Session2 = sessionmaker(bind=engine2)
            session2 = Session2()  # session instance

            filtering_dict = {key: value for key, value in filter_options.items() if value}
            practitioners, tot_count = Practitioner.get_practitioner(session1, session2, filtering_dict)
            
            if practitioners:
                st.subheader(f"{tot_count} Practitioner(s) found:")
                for i in range(len(practitioners)):
                    st.write(f"Employee ID: {practitioners[i].EmployeeID}")
                    st.write(f"Department ID: {practitioners[i].DepartmentID}")
                    st.write(f"Last Name: {practitioners[i].LastName}")
                    st.write(f"First Name: {practitioners[i].FirstName}")
                    st.write(f"Title: {practitioners[i].Title}")
                    st.write(f"License Number: {practitioners[i].LicenseNumber}")
                    st.write(f"Specialty: {practitioners[i].Specialty}")
                    st.write("---")
            else:
                st.write("No Practitioners found matching the filtering criteria.")

    
    # Receptionists Tab
    with tab5:
        st.title('Receptionists')
        st.subheader("Receptionist Information")

        filter_options = {
            "EmployeeID": st.number_input("Employee ID", value=None, step=1, key="Get Employee ID, Receptionist"),
            "DepartmentID": st.number_input("Department ID", value=None, step=1, key="Get Department ID, Receptionist"),
            "LastName": st.text_input("Last Name", value=None, key="Get Last Name, Receptionist"),
            "FirstName": st.text_input("First Name", value=None, key="Get First Name, Receptionist")
            }

        if st.button("Retrieve Receptionist Information"):
            # create session class
            engine1 = create_engine(engine_urls[1])
            Session1 = sessionmaker(bind=engine1)
            session1 = Session1()  # session instance
            
            engine2 = create_engine(engine_urls[0])
            Session2 = sessionmaker(bind=engine2)
            session2 = Session2()  # session instance

            filtering_dict = {key: value for key, value in filter_options.items() if value}
            receptionists, tot_count = Reception.get_receptionist(session1, session2, filtering_dict)
            
            if receptionists:
                st.subheader(f"{tot_count} Receptionist(s) found:")
                for i in range(len(receptionists)):
                    st.write(f"Department ID: {receptionists[i].DepartmentID}")
                    st.write(f"Employee ID: {receptionists[i].EmployeeID}")
                    st.write(f"Last Name: {receptionists[i].LastName}")
                    st.write(f"First Name: {receptionists[i].FirstName}")
                    st.write("---")
            else:
                st.write("No Receptionists found matching the filtering criteria.")

    # Departments Tab
    with tab6:
        st.title('Departments')
        st.subheader("Department Information")

        filter_options = {
            "DepartmentID": st.number_input("Department ID", value=None, step=1, key="Get Department ID, departments"),
            "DepartmentName": st.text_input("Department Name", key="Get Department Name, departments"),
            "TotalPractitioners": st.number_input("Total Practitioners", value=None, step=1, key="Get Department Practitioners, departments"),
            "TotalReceptionists": st.number_input("Total Receptionists", value=None, step=1, key="Get Department Receptionists, departments"),
            "TotalRooms": st.number_input("Total Rooms", value=None, step=1, key="Get Department Rooms, departments")
            }

        if st.button("Retrieve Department Information"):            
            # create session class
            engine1 = create_engine(engine_urls[1])
            Session1 = sessionmaker(bind=engine1)
            session1 = Session1()  # session instance

            engine2 = create_engine(engine_urls[0])
            Session2 = sessionmaker(bind=engine2)
            session2 = Session2()  # session instance

            filtering_dict = {key: value for key, value in filter_options.items() if value}
            departments, total_count = Department.get_department(session1, session2, filtering_dict)

            if departments:
                st.subheader(f"{total_count} Department(s) found:")
                for i in range(len(departments)):
                    st.write(f"Department ID: {departments[i].DepartmentID}")
                    st.write(f"Department Name: {departments[i].DepartmentName}")
                    st.write(f"Total Practitioners: {departments[i].TotalPractitioners}")
                    st.write(f"Total Receptionists: {departments[i].TotalReceptionists}")
                    st.write(f"Total Rooms: {departments[i].TotalRooms}")
                    st.write("---")

            else:
                st.write("No Departments found matching the filtering criteria.")


if __name__ == "__main__":
    if login():
        home_page()

