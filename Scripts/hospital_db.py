import mysql.connector
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
from sqlalchemy import func
from sqlalchemy.sql import select
from sqlalchemy.sql import and_
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import joinedload
import sys
import json
import itertools
import getpass

# declare base
Base = declarative_base()

# initializing global login variables
logged_in = False
username = None
password = None
# engine_urls = {}

# globally defined engine url dict
# comment out if using login function
engine_urls = {0: 'mysql+mysqlconnector://root:@localhost/database1',
               1: 'mysql+mysqlconnector://root:@localhost/database2'}


def login():
    """Login function that prompts user for MySQL username and password, checks that they are valid,
    and creates the engine urls for the databases used in this project."""
    global logged_in
    global username
    global password
    global engine_urls
    while not logged_in:
        input_username = input("Enter MySQL username: ")
        input_password = getpass.getpass("Enter MySQL password: ")
        # check if username and password valid for mysql
        try:
            connection = mysql.connector.connect(
                host='localhost',
                user=input_username,
                password=input_password,
            )
            if connection.is_connected():
                print("Successfully connected to MySQL server")
                connection.close()
                logged_in = True
                username = input_username  # update global vars
                password = input_password
                engine_urls = {0: f'mysql+mysqlconnector://{username}:{password}@localhost/database1',
                              1: f'mysql+mysqlconnector://{username}:{password}@localhost/database2'}
        except mysql.connector.Error as e:
            print("Failed to connect to MySQL server:", e)

    return username, password


def hash_department(hash_val):
    """Hash on DepartmentID to determine which database to store input data in."""
    return hash_val % 2


# define a class for each table with table functions
class Department(Base):
    __tablename__ = 'Departments'
    DepartmentID = Column(Integer, primary_key=True)  # primary_key ensures it is unique
    DepartmentName = Column(String(30), unique=True)
    TotalPractitioners = Column(Integer, default=0)
    TotalReceptionists = Column(Integer, default=0)
    TotalRooms = Column(Integer, nullable=False)

    # establishing one to many relationships with appointments, reception, and practitioner tables
    appointments = relationship("Appointment", back_populates="department")
    reception = relationship("Reception", back_populates="department_r")
    practitioner = relationship("Practitioner", back_populates="department_p")

    @classmethod
    def add_department(cls, session, dept_dict):
        """
        Function to add data to the department table.
        :param session: The session for the database created based on the hash value.
        :param dept_dict: the json object with key value pairs to add to department where the keys are
        attribute names and values are the values to add for the given row.
        :return returns the new department row added
        """
        try:
            new_department = cls(
                DepartmentID=dept_dict['DepartmentID'],
                DepartmentName=dept_dict['DepartmentName'],
                # TotalEmployees=dept_dict['TotalEmployees'],
                TotalRooms=dept_dict['TotalRooms'])

            session.add(new_department)
            session.commit()

            # calculate total practitioners
            total_practitioners = session.query(Practitioner).filter_by\
                (DepartmentID=new_department.DepartmentID).count()

            # calculate total receptionists
            total_receptionists = session.query(Reception).filter_by \
                (DepartmentID=new_department.DepartmentID).count()

            # update the TotalEmployees attribute
            new_department.TotalPractitioners = total_practitioners
            new_department.TotalReceptionists = total_receptionists
            session.commit()

            return new_department

        except Exception as e:
            session.rollback()
            print("An error occurred while adding the department:", e)
            return None

    @classmethod
    def modify_department(cls, session, deptID, new_values_dict):
        """
        Function to modify values, except for the ID itself, in departments.
        :param session: The session for the database created based on the hash value.
        :param deptID: The ID of the department to update values for.
        :param new_values_dict: the json object with key value pairs where the keys are attribute names to update
        and the values are the new values.
        :return True or False based on success of modification.
        """
        try:
            department = session.query(cls).filter_by(DepartmentID=deptID).first()

            if department:  # update all columns where the key exists in new_values_dict
                # update values
                for key, value in new_values_dict.items():
                    if key not in ["DepartmentID", "TotalPractitioners", "TotalReceptionists"]:  # cannot change these
                        setattr(department, key, value)
                    else:
                        print("Cannot modify DepartmentID, TotalPractitioners, or TotalReceptionists.")

                # commit the changes to the database
                session.commit()
                return True
            else:
                return False
        except Exception as e:
            raise Exception("An error occurred while modifying departments:", e)

    @classmethod
    def delete_department(cls, session, deptID):
        """
        Function to delete departments.
        :param session: The session for the database created based on the hash value.
        :param deptID: The ID of the department to delete.
        :return True/False to indicate success of operation
        """
        try:
            department = session.query(cls).filter_by(DepartmentID=deptID).first()

            if department:
                session.delete(department)  # delete if department id exists in table
                session.commit()  # commit changes
                return True  # return true if successful
            else:
                return False
        except Exception as e:
            raise Exception("An error occurred while deleting from departments:", e)

    @classmethod
    def get_department(cls, session1, session2, filtering_dict=None):
        """
        Function to retrieve departments from the databases. Can either retrieve all departments or
        a selection based on provided filtering criteria.
        :param session1: session for database 1
        :param session2: session for database 2
        :param filtering_dict: Filtering criteria (optional). If not provided returns all departments.
        :return The departments retrieved from the criteria and the total count of departments that meet the criteria.
        """
        try:
            query1 = session1.query(cls)
            query2 = session2.query(cls)

            # apply filter requirements if filtering_dict is provided
            if filtering_dict:
                for key, value in filtering_dict.items():
                    query1 = query1.filter(getattr(cls, key) == value)
                    query2 = query2.filter(getattr(cls, key) == value)

            # retrieve departments
            departments = []
            departments1 = query1.all()
            departments.extend(departments1)
            departments2 = query2.all()
            departments.extend(departments2)

            total_count = len(departments)

            return departments, total_count

        except Exception as e:
            raise Exception("An error occurred while retrieving data from departments:", e)


class Appointment(Base):
    __tablename__ = 'Appointments'
    AppointmentID = Column(Integer, primary_key=True, autoincrement=True)
    ReceptionistID = Column(Integer, ForeignKey("Receptionists.EmployeeID", onupdate="CASCADE", ondelete="CASCADE"))
    PatientID = Column(Integer, ForeignKey("Patients.PatientID", onupdate="CASCADE", ondelete="CASCADE"))
    PractitionerID = Column(Integer, ForeignKey("Practitioners.EmployeeID", onupdate="CASCADE", ondelete="CASCADE"))
    DepartmentID = Column(Integer, ForeignKey('Departments.DepartmentID', onupdate="CASCADE", ondelete="CASCADE"))
    AppointmentDate = Column(Date, nullable=False)
    AppointmentTime = Column(Time, nullable=False)
    Notes = Column(String(500))

    # composite FK reference to patients to make sure that a patient isnt added in an appointment for a department
    # where they are not added as a patient
    __table_args__ = (
        ForeignKeyConstraint(['PatientID', 'DepartmentID'], ['Patients.PatientID', 'Patients.DepartmentID'],
                             onupdate='CASCADE', ondelete='CASCADE'),
        UniqueConstraint('PractitionerID', 'AppointmentDate', 'AppointmentTime'),
    )

    # establishing one to many relationships
    department = relationship("Department", back_populates="appointments")
    patient_a = relationship("Patient", primaryjoin="Appointment.PatientID == Patient.PatientID")
    practitioner_a = relationship("Practitioner")

    @classmethod
    def add_appointment(cls, session, appt_dict):
        """
        Function to add appointments to the appointment table.
        :param session: the session for the database based on the hash value of the department ID
        :param appt_dict: the json object with key value pairs where the keys are the names of the
        attributes and the values are the values to insert for those attributes.
        :return: returns the new appointment added
        """
        try:
            new_appointment = cls(
                ReceptionistID=appt_dict['ReceptionistID'],
                PatientID=appt_dict['PatientID'],
                PractitionerID=appt_dict['PractitionerID'],
                DepartmentID=appt_dict['DepartmentID'],
                AppointmentDate=appt_dict['AppointmentDate'],
                AppointmentTime=appt_dict['AppointmentTime'],
                Notes=appt_dict['Notes']
            )

            session.add(new_appointment)
            session.commit()

            return new_appointment

        except Exception as e:
            session.rollback()
            print("An error occurred while adding the appointment:", e)
            return None

    @classmethod
    def modify_appointment(cls, session1, session2, filter_attributes_dict, new_values_dict):
        """
        Function to modify values in the appointments table in either databse. As appointmentID is
        auto-incremented it does not allow for updating the appointment ID.
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filter_attributes_dict: json object with key value pairs with the attributes and values for those
        attributes that specify the rows to update.
        :param new_values_dict: json object with key value pairs to specify the attributes to update and the new
        values to insert for those attributes.
        :return: True/False to indicate the success of the operation
        """
        try:
            appointments1 = session1.query(cls).filter_by(**filter_attributes_dict).all()
            appointments2 = session2.query(cls).filter_by(**filter_attributes_dict).all()

            if appointments1 or appointments2:
                for app in appointments1:
                    for key, value in new_values_dict.items():
                        if key not in ["AppointmentID", "DepartmentID"]:
                            setattr(app, key, value)
                        else:
                            print("Cannot modify AppointmentID or DepartmentID.")

                # update values for each appointment matching the filter attributes in database 2
                for app in appointments2:
                    for key, value in new_values_dict.items():
                        if key not in ["AppointmentID", "DepartmentID"]:
                            setattr(app, key, value)
                        else:
                            print("Cannot modify AppointmentID or DepartmentID.")

                # commit the changes to both databases
                session1.commit()
                session2.commit()
                return True  # success
            else:
                return False  # no appointments found matching the filter attributes in either database

        except Exception as e:
            raise Exception("An error occurred while modifying appointments:", e)

    @classmethod
    def delete_appointment(cls, session1, session2, filter_attributes_dict):
        """
        Function to delete appointments in either database.
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filter_attributes_dict: json object with key value pairs to specify requirements for the rows to delete.
        :return: True/False to indicate the success of the operation
        """
        try:
            appointments1 = session1.query(cls).filter_by(**filter_attributes_dict).all()
            appointments2 = session2.query(cls).filter_by(**filter_attributes_dict).all()

            if appointments1 or appointments2:
                # delete appointments matching the filter attributes in database 1
                for appointment in appointments1:
                    session1.delete(appointment)

                # delete appointments matching the filter attributes in database 2
                for appointment in appointments2:
                    session2.delete(appointment)

                # commit the changes to both databases
                session1.commit()
                session2.commit()
                return True  # Success
            else:
                return False  # No appointments found matching the filter attributes in either database
        except Exception as e:
            raise Exception("An error occurred while deleting from appointments:", e)

    @classmethod
    def get_appointment(cls, session1, session2, filtering_dict=None):
        """
        Function to retrieve appointments from both databases. If no filtering dict provided, it retrieves
        all appointments in both databases or if filtering_dict is provided it retrieves all appointments
        that meet the provided criteria.
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filtering_dict: json object with key value pairs where the keys represent attribute names and
        the values represent the values for those attributes you want to retrieve rows for.
        :return: returns the appointments specified and a total count of said appointments.
        """
        try:
            query1 = session1.query(cls)
            query2 = session2.query(cls)

            # joining attributes from referenced tables
            query1 = query1.join(cls.patient_a) \
                .join(cls.practitioner_a) \
                .join(cls.department)

            query2 = query2.join(cls.patient_a) \
                .join(cls.practitioner_a) \
                .join(cls.department)

            # specify columns to load from the Patient, Practitioner, and Department tables
            columns_to_load = {
                Patient: ['FirstName', 'LastName'],
                Practitioner: ['FirstName', 'LastName'],
                Department: ['DepartmentName']
            }

            # join the tables with specified attributes to load
            query1 = query1.options(
                joinedload(cls.department).load_only(*columns_to_load[Department]),
                joinedload(cls.patient_a).load_only(*columns_to_load[Patient]),
                joinedload(cls.practitioner_a).load_only(*columns_to_load[Practitioner]))
            query2 = query2.options(
                joinedload(cls.department).load_only(*columns_to_load[Department]),
                joinedload(cls.patient_a).load_only(*columns_to_load[Patient]),
                joinedload(cls.practitioner_a).load_only(*columns_to_load[Practitioner]))

            # apply filter requirements
            if filtering_dict:
                for key, value in filtering_dict.items():
                    query1 = query1.filter(getattr(cls, key) == value)
                    query2 = query2.filter(getattr(cls, key) == value)

            # retrieve appointments
            appointments = []
            appointments1 = query1.all()
            appointments2 = query2.all()
            appointments.extend(appointments1)
            appointments.extend(appointments2)

            total_count = len(appointments)

            return appointments, total_count

        except Exception as e:
            raise Exception("An error occurred while retrieving data from appointments:", e)


class Reception(Base):
    __tablename__ = 'Receptionists'
    EmployeeID = Column(Integer, primary_key=True, autoincrement=False)
    LastName = Column(String(100), nullable=False)
    FirstName = Column(String(100), nullable=False)
    DepartmentID = Column(Integer, ForeignKey('Departments.DepartmentID', onupdate="CASCADE", ondelete="CASCADE"))

    # add constraint to make sure employeeid is 6 digits
    check_employee_id = CheckConstraint('length(EmployeeID) = 6')
    __table_args__ = (check_employee_id,)

    # one to many relation with department, assumes each receptionist is hired by at most one deptarment
    department_r = relationship("Department", back_populates="reception")

    @classmethod
    def add_receptionist(cls, session, employee_dict):
        """
        Function to insert data to the receptionists table
        :param session: session instance for the database based on the hash value of DepartmentID
        :param employee_dict: json object with key value pairs where the key is the attribute name and the value
        is the value to insert for that attribute.
        :return: returns the row added
        """
        try:
            new_employee = cls(
                EmployeeID=employee_dict['EmployeeID'],
                LastName=employee_dict['LastName'],
                FirstName=employee_dict['FirstName'],
                DepartmentID=employee_dict['DepartmentID'],

            )
            session.add(new_employee)
            session.commit()

            return new_employee

        except Exception as e:
            session.rollback()
            print("An error occurred while adding the receptionist:", e)
            return None

    @classmethod
    def modify_receptionist(cls, session1, session2, filter_attributes_dict, new_values_dict):
        """
        Function to modify values in the receptionists table in either database
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filter_attributes_dict: json object with key value pairs to represent the attributes and value criteria
        for rows that you want to update
        :param new_values_dict: json object with key value pairs to represent the attributes you want to update
        with values you want to update them to
        :return: True/False to indicate the success of the operation
        """
        try:
            receptionists1 = session1.query(cls).filter_by(**filter_attributes_dict).all()
            receptionists2 = session2.query(cls).filter_by(**filter_attributes_dict).all()

            if receptionists1 or receptionists2:
                # update values for each receptionist matching the filter attributes in database 1
                for rec in receptionists1:
                    if 'DepartmentID' in new_values_dict:
                        print("dept")
                        # Get the original and new departmentID value  and hash val
                        original_dept_id = rec.DepartmentID
                        new_dept_id = new_values_dict['DepartmentID']
                        original_hash_val = hash_department(original_dept_id)
                        new_hash_val = hash_department(new_dept_id)

                        # if the databases are different
                        if original_hash_val != new_hash_val:
                            original_values = {attr: getattr(rec, attr) for attr in rec.__table__.columns.keys()}

                            # update the values
                            for key, value in new_values_dict.items():
                                original_values[key] = value

                            # set the new DepartmentID value
                            original_values['DepartmentID'] = new_dept_id

                            new_rec = cls(**original_values)

                            # add the new receptionist object to the other session's database
                            session2.add(new_rec)
                            session2.commit()  # commit the changes to the other session's database

                            # remove the original receptionist object from the current session's database
                            session1.delete(rec)
                            session1.commit()
                        else:
                            for key, value in new_values_dict.items():
                                setattr(rec, key, value)

                    else:
                        for key, value in new_values_dict.items():
                            setattr(rec, key, value)

                # update values for each receptionist matching the filter attributes in database 2
                for rec in receptionists2:
                    if 'DepartmentID' in new_values_dict:
                        print("dept")
                        # Get the original and new departmentID value  and hash val
                        original_dept_id = rec.DepartmentID
                        new_dept_id = new_values_dict['DepartmentID']
                        original_hash_val = hash_department(original_dept_id)
                        new_hash_val = hash_department(new_dept_id)

                        # if the databases are different
                        if original_hash_val != new_hash_val:
                            original_values = {attr: getattr(rec, attr) for attr in rec.__table__.columns.keys()}

                            # update the values
                            for key, value in new_values_dict.items():
                                original_values[key] = value

                            # set the new DepartmentID value
                            original_values['DepartmentID'] = new_dept_id

                            new_rec = cls(**original_values)

                            # add the new receptionist object to the other session's database
                            session1.add(new_rec)
                            session1.commit()  # Commit the changes to the other session's database

                            # remove the original receptionist object from the current session's database
                            session2.delete(rec)
                            session2.commit()
                        else:
                            for key, value in new_values_dict.items():
                                setattr(rec, key, value)
                    else:
                        for key, value in new_values_dict.items():
                            setattr(rec, key, value)

                # commit the changes to both databases
                session1.commit()
                session2.commit()

                return True  # success
            else:
                return False  # no receptionists found matching the filter attributes in either database

        except Exception as e:
            raise Exception("An error occurred while modifying receptionists:", e)

    @classmethod
    def delete_receptionist(cls, session1, session2, filter_attributes_dict):
        """
        Function to delete receptionists from the receptionists' table in either database
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filter_attributes_dict: json object with key value pairs where the keys represent
        the attributes and the values represent the values for the rows to be deleted
        :return: True/False to indicate the success of the operation
        """
        try:
            receptionist1 = session1.query(cls).filter_by(**filter_attributes_dict).all()
            receptionist2 = session2.query(cls).filter_by(**filter_attributes_dict).all()

            if receptionist1 or receptionist2:
                # delete receptionists matching the filter attributes in database 1
                for rec in receptionist1:
                    session1.delete(rec)

                # delete receptionists matching the filter attributes in database 2
                for rec in receptionist2:
                    session2.delete(rec)

                # commit the changes to both databases
                session1.commit()
                session2.commit()
                return True  # success
            else:
                return False  # no receptionists found matching the filter attributes in either database

        except Exception as e:
            raise Exception("An error occurred while deleting from receptionists:", e)

    @classmethod
    def get_receptionist(cls, session1, session2, filtering_dict=None):
        """
        Function to retrieve receptionists from either database. Either retrieves all receptionists if no filtering_dict
        is provided or a subset based on the filtering criteria.
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filtering_dict: json object with key value pairs where the keys are the attribute names and the
        values are the value criteria for the rows to be retrieved
        :return: the retrieved receptionists and a total count of the said receptionists
        """
        try:
            query1 = session1.query(cls)
            query2 = session2.query(cls)

            # joining attributes from referenced tables
            query1 = query1.join(cls.department_r)
            query2 = query2.join(cls.department_r)

            # specify columns to load from the Patient, Practitioner, and Department tables
            columns_to_load = {
                Department: ['DepartmentName']
            }

            # join the tables with specified attributes to load
            query1 = query1.options(
                joinedload(cls.department_r).load_only(*columns_to_load[Department])
            )
            query2 = query2.options(
                joinedload(cls.department_r).load_only(*columns_to_load[Department])
            )

            # apply filter requirements
            if filtering_dict:
                for key, value in filtering_dict.items():
                    query1 = query1.filter(getattr(cls, key) == value)
                    query2 = query2.filter(getattr(cls, key) == value)

            # retrieve receptionists
            receptionists = []
            receptionists1 = query1.all()
            receptionists2 = query2.all()
            receptionists.extend(receptionists1)
            receptionists.extend(receptionists2)

            total_count = len(receptionists)

            return receptionists, total_count

        except Exception as e:
            raise Exception("An error occurred while retrieving data from receptionists:", e)


class Practitioner(Base):
    __tablename__ = 'Practitioners'
    EmployeeID = Column(Integer, primary_key=True, autoincrement=False)
    LastName = Column(String(100), nullable=False)
    FirstName = Column(String(100), nullable=False)
    LicenseNumber = Column(Integer, unique=True)
    Title = Column(String(100), nullable=False)
    DepartmentID = Column(Integer, ForeignKey('Departments.DepartmentID', onupdate="CASCADE", ondelete="CASCADE"))
    Specialty = Column(String(200))

    check_employee_id = CheckConstraint('length(EmployeeID) = 6')
    __table_args__ = (check_employee_id,)

    # relationship with departments
    department_p = relationship("Department", back_populates="practitioner")

    @classmethod
    def add_practitioner(cls, session, employee_dict):
        """
        Function to insert data into the practitioners table.
        :param session: session instance of the database based on the hash value of the DepartmentID
        :param employee_dict: json object with key value pairs where the keys represent the attribute names
        and the values represent the values to be inserted for said attributes
        :return: returns the new row added
        """
        try:
            new_employee = cls(
                EmployeeID=employee_dict['EmployeeID'],
                LastName=employee_dict['LastName'],
                FirstName=employee_dict['FirstName'],
                LicenseNumber=employee_dict['LicenseNumber'],
                Title=employee_dict['Title'],
                DepartmentID=employee_dict['DepartmentID'],
                Specialty=employee_dict['Specialty']

            )
            session.add(new_employee)
            session.commit()

            return new_employee

        except Exception as e:
            session.rollback()
            print("An error occurred while adding the practitioner:", e)
            return None

    @classmethod
    def modify_practitioner(cls, session1, session2, filter_attributes_dict, new_values_dict):
        """
        Function to modify data in the practitioners' table in either database
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filter_attributes_dict: json object with key value pairs where the keys represent the attribute names
        and the values represent the value criteria for the rows to be updated
        :param new_values_dict: json object with key value pairs where the keys represent the attribute names
        and the values represent the new values to insert to said attributes
        :return: True/False to indicate the success of the operation
        """
        try:
            practitioner1 = session1.query(cls).filter_by(**filter_attributes_dict).all()
            practitioner2 = session2.query(cls).filter_by(**filter_attributes_dict).all()

            if practitioner1 or practitioner2:
                # update values for each practitioner matching the filter attributes in database 1
                for pra in practitioner1:
                    if 'DepartmentID' in new_values_dict:
                        # get the original and new departmentID value  and hash val
                        original_dept_id = pra.DepartmentID
                        new_dept_id = new_values_dict['DepartmentID']
                        original_hash_val = hash_department(original_dept_id)
                        new_hash_val = hash_department(new_dept_id)

                        # if the databases are different
                        if original_hash_val != new_hash_val:
                            original_values = {attr: getattr(pra, attr) for attr in pra.__table__.columns.keys()}

                            # update the values
                            for key, value in new_values_dict.items():
                                original_values[key] = value

                            # set the new DepartmentID value
                            original_values['DepartmentID'] = new_dept_id

                            new_pra = cls(**original_values)

                            # add the new practitioner object to the other session's database
                            session2.add(new_pra)
                            session2.commit()  # commit the changes to the other session's database

                            # remove the original practitioner object from the current session's database
                            session1.delete(pra)
                            session1.commit()
                        else:
                            for key, value in new_values_dict.items():
                                setattr(pra, key, value)

                    else:
                        for key, value in new_values_dict.items():
                            setattr(pra, key, value)

                # update values for each practitioner matching the filter attributes in database 2
                for pra in practitioner2:
                    if 'DepartmentID' in new_values_dict:
                        # get the original and new departmentID value  and hash val
                        original_dept_id = pra.DepartmentID
                        new_dept_id = new_values_dict['DepartmentID']
                        original_hash_val = hash_department(original_dept_id)
                        new_hash_val = hash_department(new_dept_id)

                        # if the databases are different
                        if original_hash_val != new_hash_val:
                            original_values = {attr: getattr(pra, attr) for attr in pra.__table__.columns.keys()}

                            # update the values
                            for key, value in new_values_dict.items():
                                original_values[key] = value

                            # set the new DepartmentID value
                            original_values['DepartmentID'] = new_dept_id

                            new_pra = cls(**original_values)

                            # add the new practitioner object to the other session's database
                            session1.add(new_pra)
                            session1.commit()  # commit the changes to the other session's database

                            # remove the original practitioner object from the current session's database
                            session2.delete(pra)
                            session2.commit()
                        else:
                            for key, value in new_values_dict.items():
                                setattr(pra, key, value)

                    else:
                        for key, value in new_values_dict.items():
                            setattr(pra, key, value)

                # commit the changes to both databases
                session1.commit()
                session2.commit()
                return True  # success
            else:
                return False  # no practitioners found matching the filter attributes in either database

        except Exception as e:
            raise Exception("An error occurred while modifying practitioners:", e)

    @classmethod
    def delete_practitioner(cls, session1, session2, filter_attributes_dict):
        """
        Function to delete practitioners from either database
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filter_attributes_dict: json object with key value pairs where the keys represent the attribute names
        and the values represent the value criteria said attributes for the rows to be deleted
        :return: True/False to indicate the success of the operation
        """
        try:
            practitioner1 = session1.query(cls).filter_by(**filter_attributes_dict).all()
            practitioner2 = session2.query(cls).filter_by(**filter_attributes_dict).all()

            if practitioner1 or practitioner2:
                # delete practitioners matching the filter attributes in database 1
                for prac in practitioner1:
                    session1.delete(prac)

                # delete practitioners matching the filter attributes in database 2
                for prac in practitioner2:
                    session2.delete(prac)

                # commit the changes to both databases
                session1.commit()
                session2.commit()
                return True  # success
            else:
                return False  # no practitioners found matching the filter attributes in either database

        except Exception as e:
            raise Exception("An error occurred while deleting from practitioners:", e)

    @classmethod
    def get_practitioner(cls, session1, session2, filtering_dict=None):
        """
        Function to retrieve practitioners from either database. Either retrieves all if no filtering_dict provided
        or a subset based on provided filtering criteria.
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filtering_dict: json object with key value pairs where the keys represent the attribute names and
        the values represent the value criteria for the rows to be retrieved
        :return: the practitioners retrieved based on given criteria and a total count of said practitioners
        """
        try:
            query1 = session1.query(cls)
            query2 = session2.query(cls)

            # joining attributes from referenced tables
            query1 = query1.join(cls.department_p)
            query2 = query2.join(cls.department_p)

            # specify columns to load from the Patient, Practitioner, and Department tables
            columns_to_load = {
                Department: ['DepartmentName']
            }

            # join the tables with specified attributes to load
            query1 = query1.options(
                joinedload(cls.department_p).load_only(*columns_to_load[Department]))
            query2 = query2.options(
                joinedload(cls.department_p).load_only(*columns_to_load[Department]))

            # apply filter requirements
            if filtering_dict:
                for key, value in filtering_dict.items():
                    query1 = query1.filter(getattr(cls, key) == value)
                    query2 = query2.filter(getattr(cls, key) == value)

            # retrieve practitioners
            practitioners = []
            practitioners1 = query1.all()
            practitioners2 = query2.all()
            practitioners.extend(practitioners1)
            practitioners.extend(practitioners2)

            total_count = len(practitioners)

            return practitioners, total_count

        except Exception as e:
            raise Exception("An error occurred while retrieving data from practitioners:", e)


class Patient(Base):
    __tablename__ = 'Patients'
    PatientID = Column(Integer, autoincrement=False, nullable=False)
    LastName = Column(String(100), nullable=False)
    FirstName = Column(String(100), nullable=False)
    DOB = Column(Date, nullable=False)
    Gender = Column(String(25))
    SchedulingState = Column(String(50), default="Unscheduled", server_default="Unscheduled")
    DepartmentID = Column(Integer, ForeignKey("Departments.DepartmentID", onupdate="CASCADE", ondelete="CASCADE"))
    Insurance = Column(String(20))
    PastProcedures = Column(String(500))
    Notes = Column(String(500))

    department_pa = relationship("Department")  # define relationship with departments

    check_patient_id = CheckConstraint('length(PatientID) = 4')  # constraint to ensure that patient id is 4 digits

    # define composite primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint('PatientID', 'DepartmentID'),
        check_patient_id,
    )

    @classmethod
    def add_patient(cls, session, patient_dict):
        """
        Function to insert data into the patients table
        :param session: session instance for the given database based on the hash value of the DepartmentID
        :param patient_dict: json object with key value pairs where the keys represent the attributes and the values
        represent the values to be inserted for said attributes
        :return: returns the new row added
        """
        try:
            new_patient = cls(
                PatientID=patient_dict['PatientID'],
                LastName=patient_dict['LastName'],
                FirstName=patient_dict['FirstName'],
                DOB=patient_dict['DOB'],
                Gender=patient_dict['Gender'],
                # SchedulingState=patient_dict['SchedulingState'],
                DepartmentID=patient_dict['DepartmentID'],
                Insurance=patient_dict['Insurance'],
                PastProcedures=patient_dict['PastProcedures'],
                Notes=patient_dict['Notes']
            )

            session.add(new_patient)
            session.commit()

            # check if patient has been scheduled to add scheduling state
            appt_count = session.query(Appointment).filter_by(PatientID=new_patient.PatientID,
                                                              DepartmentID=new_patient.DepartmentID).count()
            if appt_count > 0:
                new_patient.SchedulingState = "Scheduled"
            else:
                new_patient.SchedulingState = "Unscheduled"

            session.commit()

            return new_patient

        except Exception as e:
            session.rollback()
            print("An error occurred while adding the patient:", e)
            return None

    @classmethod
    def modify_patient(cls, session1, session2, filter_attributes_dict, new_values_dict):
        """
        Function to modify data in the patients' table in either database
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filter_attributes_dict: json object with key value pairs where the keys represent the attribute names
        and the values represent the value criteria for the rows to be updated
        :param new_values_dict: json object with key value pairs where the keys represent the attribute names
        and the values represent the new values to be inserted for said attributes
        :return: True/False to indicate the success of the operation
        """
        try:
            patient1 = session1.query(cls).filter_by(**filter_attributes_dict).all()
            patient2 = session2.query(cls).filter_by(**filter_attributes_dict).all()

            if patient1 or patient2:
                for patient in patient1:
                    for key, value in new_values_dict.items():
                        if key not in ["SchedulingState", "DepartmentID"]:
                            setattr(patient, key, value)
                        else:
                            print("Cannot modify SchedulingState or DepartmentID.")

                for patient in patient2:
                    for key, value in new_values_dict.items():
                        if key not in ["SchedulingState", "DepartmentID"]:
                            setattr(patient, key, value)
                        else:
                            print("Cannot modify SchedulingState or DepartmentID.")

                # commit the changes to both databases
                session1.commit()
                session2.commit()
                return True  # success
            else:
                return False  # no patients found matching the filter attributes in either database

        except Exception as e:
            raise Exception("An error occurred while modifying patients:", e)

    @classmethod
    def delete_patient(cls, session1, session2, filter_attributes_dict):
        """
        Function to delete data from the patients' table in either database
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filter_attributes_dict: json object with key value pairs where the keys represent the attribute names
        and the values represent the value criteria for said attributes for the rows to be deleted
        :return: True/False to indicate the success of the operation
        """
        try:
            patient1 = session1.query(cls).filter_by(**filter_attributes_dict).all()
            patient2 = session2.query(cls).filter_by(**filter_attributes_dict).all()

            if patient1 or patient2:
                # delete patients matching the filter attributes in database 1
                for pa in patient1:
                    session1.delete(pa)

                # delete patients matching the filter attributes in database 2
                for pa in patient2:
                    session2.delete(pa)

                # commit the changes to both databases
                session1.commit()
                session2.commit()
                return True  # success
            else:
                return False  # no patients found matching the filter attributes in either database

        except Exception as e:
            raise Exception("An error occurred while deleting from patients:", e)

    @classmethod
    def get_patient(cls, session1, session2, filtering_dict=None):
        """
        Function to retrieve patients data from either database. Either retrieves all patients if no filtering_dict
        provided or a subset based on filtering criteria
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param filtering_dict: json object with key value pairs where the keys represent the attributes and the values
        represent the value criteria of said attributes for the rows to be retrieved
        :return: the retrieved patients and a total count of said patients
        """
        try:
            query1 = session1.query(cls)
            query2 = session2.query(cls)

            # joining attributes from referenced tables
            query1 = query1.join(cls.department_pa)
            query2 = query2.join(cls.department_pa)

            # specify columns to load from the Patient, Practitioner, and Department tables
            columns_to_load = {
                Department: ['DepartmentName']
            }

            # join the tables with specified attributes to load
            query1 = query1.options(
                joinedload(cls.department_pa).load_only(*columns_to_load[Department]))
            query2 = query2.options(
                joinedload(cls.department_pa).load_only(*columns_to_load[Department]))

            # apply filter requirements
            if filtering_dict:
                for key, value in filtering_dict.items():
                    query1 = query1.filter(getattr(cls, key) == value)
                    query2 = query2.filter(getattr(cls, key) == value)

            # retrieve patients
            patients = []
            patient1 = query1.all()
            patient2 = query2.all()
            patients.extend(patient1)
            patients.extend(patient2)

            total_count = len(patients)

            return patients, total_count

        except Exception as e:
            raise Exception("An error occurred while retrieving data from patients:", e)


class PatientOf(Base):
    __tablename__ = 'Patient_Of'
    # ID = Column(Integer, primary_key=True, autoincrement=True)
    PatientID = Column(Integer, ForeignKey('Patients.PatientID',
                                           onupdate="CASCADE", ondelete="CASCADE"))
    PractitionerID = Column(Integer, ForeignKey('Practitioners.EmployeeID',
                                                onupdate="CASCADE", ondelete="CASCADE"))
    # composite primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint('PatientID', 'PractitionerID'),
    )

    # define relationships
    patient = relationship("Patient", uselist=True)
    practitioner_2 = relationship("Practitioner", uselist=True)

    @classmethod
    def get_patients_of(cls, session1, session2, practitioner_id, attribute_names=None):
        """
        Function to retrieve all patients of a given practitioner in either database
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param practitioner_id: the ID of the practitioner you wish to view patients of
        :param attribute_names: optional list of attribute names to retrieve for the patients - if you wish to view
        all patient attributes, no need to provide; however, if you for instance wish to only view first
        and last names you would provide "[FirstName, LastName]" in the command line
        :return: patients with all/specified attributes and a total count of said patients
        """
        try:
            patient_of_instances1 = session1.query(cls).filter(cls.PractitionerID == practitioner_id).all()
            patient_of_instances2 = session2.query(cls).filter(cls.PractitionerID == practitioner_id).all()

            # collect associated Patient instances for each PatientOf instance
            patients_with_attributes = []
            for instance in patient_of_instances1:
                # access the associated Patient instance through the relationship
                patients = instance.patient
                # apply filtering if filtering_dict is provided
                if attribute_names:
                    filtered_patients = []
                    for patient in patients:
                        filtered_patient = {key: getattr(patient, key) for key in attribute_names}
                        filtered_patients.append(filtered_patient)
                    patients_with_attributes.append((instance, filtered_patients))
                else:
                    patients_with_attributes.append((instance, patients))

            for instance in patient_of_instances2:
                # access the associated Patient instance through the relationship
                patients = instance.patient
                # apply filtering if filtering_dict is provided
                if attribute_names:
                    filtered_patients = []
                    for patient in patients:
                        filtered_patient = {key: getattr(patient, key) for key in attribute_names}
                        filtered_patients.append(filtered_patient)
                    patients_with_attributes.append((instance, filtered_patients))
                else:
                    patients_with_attributes.append((instance, patients))

            total_count = len(patients_with_attributes)

            return patients_with_attributes, total_count

        except Exception as e:
            raise Exception("An error occurred while retrieving patients of the practitioner:", e)

    @classmethod
    def get_practitioners_for(cls, session1, session2, patient_id, attribute_names=None):
        """
        Function to retrieve all practitioners for a given patient in either database
        :param session1: session instance for database1
        :param session2: session instance for database2
        :param patient_id: the PatientID of the patient you wish to view practitioners for
        :param attribute_names: optional list of attributes to retrieve for the practitioners - if you wish to view
        all attributes, no need to provide; however, if you for instance wish to only view first
        and last names you would provide "[FirstName, LastName]" in the command line
        :return: practitioners with all/specified attributes and a total count of said practitioners
        """
        try:
            patient_of_instances1 = session1.query(cls).filter(cls.PatientID == patient_id).all()
            patient_of_instances2 = session2.query(cls).filter(cls.PatientID == patient_id).all()

            # collect associated practitioner instances for each PatientOf instance
            practitioners_with_attributes = []
            for instance in patient_of_instances1:
                # access the associated practitioner instances through the relationship
                practitioners = instance.practitioner_2

                if attribute_names:
                    # apply filtering if attribute_names are provided
                    filtered_practitioners = []
                    for practitioner in practitioners:
                        filtered_practitioner = {key: getattr(practitioner, key) for key in attribute_names}
                        filtered_practitioners.append(filtered_practitioner)
                    practitioners_with_attributes.append((instance, filtered_practitioners))
                else:
                    practitioners_with_attributes.append((instance, practitioners))

            for instance in patient_of_instances2:
                # access the associated practitioner instances through the relationship
                practitioners = instance.practitioner_2

                if attribute_names:
                    # apply filtering if attribute_names are provided
                    filtered_practitioners = []
                    for practitioner in practitioners:
                        filtered_practitioner = {key: getattr(practitioner, key) for key in attribute_names}
                        filtered_practitioners.append(filtered_practitioner)
                    practitioners_with_attributes.append((instance, filtered_practitioners))
                else:
                    practitioners_with_attributes.append((instance, practitioners))

            total_count = len(practitioners_with_attributes)

            return practitioners_with_attributes, total_count

        except Exception as e:
            raise Exception("An error occurred while retrieving practitioners for the patient:", e)


# using event listens for to update the total practitioners' column in departments automatically
@event.listens_for(Practitioner, 'after_insert')
@event.listens_for(Practitioner, 'after_update')
@event.listens_for(Practitioner, 'after_delete')
def update_total_employees(mapper, connection, target):
    department_id = target.DepartmentID
    total_practitioners = connection.execute(select(func.count()).where(Practitioner.DepartmentID
                                                                    == department_id)).scalar()
    department_table = Department.__table__
    connection.execute(
        department_table.update()
        .where(department_table.c.DepartmentID == department_id)
        .values(TotalPractitioners=total_practitioners)
    )


# using event listens for to update the total receptionists' column in departments automatically
@event.listens_for(Reception, 'after_insert')
@event.listens_for(Reception, 'after_update')
@event.listens_for(Reception, 'after_delete')
def update_total_employees(mapper, connection, target):
    department_id = target.DepartmentID
    total_receptionists = connection.execute(select(func.count()).where(Reception.DepartmentID
                                                                    == department_id)).scalar()
    department_table = Department.__table__
    connection.execute(
        department_table.update()
        .where(department_table.c.DepartmentID == department_id)
        .values(TotalReceptionists=total_receptionists)
    )


# using event listens for to update the scheduling state column in patients by department automatically
@event.listens_for(Appointment, 'after_insert')
@event.listens_for(Appointment, 'after_update')
@event.listens_for(Appointment, 'after_delete')
def update_scheduling_state(mapper, connection, target):
    patient_id = target.PatientID
    department_id = target.DepartmentID
    total_appointments = connection.execute(select(func.count()).where(Appointment.PatientID == patient_id,
                                                                       Appointment.DepartmentID == department_id
                                                                       )).scalar()
    if total_appointments > 0:
        state = "Scheduled"
    else:
        state = "Unscheduled"
    patient_table = Patient.__table__
    connection.execute(
        patient_table.update()
        .where(patient_table.c.PatientID == patient_id, patient_table.c.DepartmentID == department_id)
        .values(SchedulingState=state))


# use event listens for to update the patient of table automatically
@event.listens_for(Appointment, 'after_insert')
@event.listens_for(Appointment, 'after_update')
@event.listens_for(Appointment, 'after_delete')
def add_patient_practitioner_pair(mapper, connection, target):
    if target.__class__.__name__ == 'Appointment':
        patient_id = target.PatientID
        practitioner_id = target.PractitionerID

        if 'after_delete' in target.__dict__:
            # check if the patient_id and practitioner_id combination exists in any appointments
            appointment_exists = connection.execute(
                select([Appointment]).where(and_(Appointment.PatientID == patient_id,
                                                 Appointment.PractitionerID == practitioner_id)).exists()).scalar()
            if not appointment_exists:
                # remove the entry from the PatientOf table
                connection.execute(PatientOf.__table__.delete().where(and_(PatientOf.PatientID ==
                                                                           patient_id, PatientOf.PractitionerID
                                                                           == practitioner_id)))
        else:
            # check if the pair exists in PatientOf
            existing_pair = connection.execute(select([PatientOf]).where(and_(
                PatientOf.PatientID == patient_id, PatientOf.PractitionerID == practitioner_id))).fetchone()

            # if the pair doesn't exist, insert a new row in PatientOf table
            if existing_pair is None:
                connection.execute(
                    PatientOf.__table__.insert().values(PatientID=patient_id, PractitionerID=practitioner_id)
                )


def main():
    # to use login function, check if user is logged in
    # global username
    # global password
    # global logged_in
    # if not logged_in:
    # username, password = login()

    # checking if sufficient arguments are provided
    if len(sys.argv) < 2:
        print("Usage: python script.py [operation] [arguments]")
    # print(len(sys.argv))

    operation = sys.argv[1].lower()  # extracting the provided operation

    # initializing variables
    json_dict = {}
    id_var = -1
    id_var2 = None
    attribute_list = None
    hash_val = None  # initializing to none
    dept_id_found = False  # track if DepartmentID is found
    query = None
    json_dict2 = None
    session = None
    session1 = None
    session2 = None

    # accessing json dict, id variables and other information provided in the command line based on the length of input
    if len(sys.argv) == 3:
        if sys.argv[2].isdigit():  # applies to modify and delete departments
            id_num = sys.argv[2]
            try:
                id_var = int(id_num)
            except Exception as e:
                raise Exception("Error encoding input:", e)
        else:  # applies to all add functions, get except for patient of if filter attributes provided
            # and all delete except department
            json_str = sys.argv[2]
            try:
                json_dict = json.loads(json_str)
            except Exception as e:
                raise Exception("Error encoding input:", e)
    elif len(sys.argv) == 4:
        if operation == "modify_department":  # applies to modify department
            # print(operation)
            id_num = sys.argv[2]
            json_str = sys.argv[3]
            try:
                id_var = int(id_num)
                json_dict = json.loads(json_str)
            except Exception as e:
                raise Exception("Error encoding input:", e)
        elif operation.startswith('modify'):  # applies to all modify except department
            json_str = sys.argv[2]
            json_str2 = sys.argv[3]
            try:
                json_dict = json.loads(json_str)
                json_dict2 = json.loads(json_str2)
            except Exception as e:
                raise Exception("Error encoding input:", e)
        elif operation.startswith('get'):  # applies to both get functions for patient of
            id_num = sys.argv[2]
            attribute_str = sys.argv[3]
            try:
                id_var = int(id_num)
                attribute_list = attribute_str.strip("[]").split(", ")
            except Exception as e:
                raise Exception("Error encoding input:", e)

    if json_dict:  # only enter if its not empty ie don't enter for delete operations
        for key, value in json_dict.items():
            if key == 'DepartmentID':
                hash_val = value
                # print(hash_val)
                dept_id_found = True
                break  # exit loop since DepartmentID is found

    # if not hash_val:  # if no hash val but the id var is the department id set hash val to id_var
    if operation == "modify_department" or operation == "delete_department":
        hash_val = id_var

    # if hash_value found, call hash functon and create a singular session to store data in the correct database
    if hash_val and (operation.startswith('add') or
                     operation == 'modify_department' or operation == 'delete_department'):
        # call hash function to create the designated engine
        db_num = hash_department(hash_val)
        engine = create_engine(engine_urls[db_num])
        # print(engine)

        # create session class
        Session = sessionmaker(bind=engine)
        session = Session()  # session instance

        # create tables if they dont exist
        Base.metadata.create_all(engine, checkfirst=True)
    else:  # creating both session instances for all functions that need to check/update/delete/retrieve data from both
        engine1 = create_engine(engine_urls[0])  # may be better to move this
        Session1 = sessionmaker(bind=engine1)
        session1 = Session1()  # session instance

        engine2 = create_engine(engine_urls[1])
        Session2 = sessionmaker(bind=engine2)
        session2 = Session2()  # session instance

        # create tables if they don't exist
        Base.metadata.create_all(engine1, checkfirst=True)
        Base.metadata.create_all(engine2, checkfirst=True)

    # call all functions for departments
    if operation == "add_department":
        required_keys = ['DepartmentID', 'DepartmentName', 'TotalRooms']  # require attributes
        if all(key in json_dict for key in required_keys):
            if Department.add_department(session, json_dict):
                print("Success! The data was added to departments.")
            else:
                print("An error occurred while adding the department.")
        else:
            print("Error. To add a new department, please specify DepartmentID, DepartmentName,"
                  " and TotalRooms in your JSON object.")
    elif operation == "modify_department":
        if Department.modify_department(session, id_var, json_dict):
            print("Success! The department data has been updated.")
        else:
            print("The department criteria does not exist or an error occurred while modifying. Please make sure to"
                  " specify the correct attribute names for modification.")
    elif operation == "delete_department":
        if Department.delete_department(session, id_var):
            print("Success! The department has been deleted.")
        else:
            print("The department does not exist or an error occurred while deleting. Please make sure to"
                  " specify the correct attribute names.")
    elif operation == "get_department":
        if json_dict:
            department, total_count = Department.get_department(session1, session2, json_dict)
        else:
            department, total_count = Department.get_department(session1, session2)

        if department:
            for dept in department:
                print("Department:")
                for column in Department.__table__.columns:
                    print(f"{column.name}: {getattr(dept, column.name)}")
                print("---------------------")
            print(f"Total count of departments that meet your criteria: {total_count}")
        else:
            print("No departments found for the given filtering criteria")

    # call all functions for the appointments table
    elif operation == "add_appointment":
        required_keys = ['ReceptionistID', 'PatientID', 'PractitionerID', 'DepartmentID',
                         'AppointmentDate', 'AppointmentTime', 'Notes']
        if all(key in json_dict for key in required_keys):
            if Appointment.add_appointment(session, json_dict):
                print("Success! The data was added to appointments.")
            else:
                print("An error occurred while adding the appointment data.")
        else:
            print("Error. To add a new appointment, please include the ReceptionistID, PatientID "
                  "PractitionerID, DepartmentID, AppointmentDate, AppointmentTime "
                  "and Notes in your JSON object.")
    elif operation == "modify_appointment":
        if Appointment.modify_appointment(session1, session2, json_dict, json_dict2):
            print("Success! The appointments data was updated.")
        else:
            print("An error occurred while modifying the appointments data. Please make sure to"
                  " specify the correct attribute names and values for modification.")
    elif operation == "delete_appointment":
        if Appointment.delete_appointment(session1, session2, json_dict):
            print("Success! The appointments that meet the criteria were deleted.")
        else:
            print("An error occurred while deleting the data from appointments. Please make sure to"
                  " specify the correct attribute names and values.")
    elif operation == "get_appointment":
        if json_dict:
            appointments, total_count = Appointment.get_appointment(session1, session2, json_dict)
        else:
            appointments, total_count = Appointment.get_appointment(session1, session2)
        if appointments:
            for appointment in appointments:
                print("Appointment:")
                for column in Appointment.__table__.columns:
                    print(f"{column.name}: {getattr(appointment, column.name)}")
                if hasattr(appointment, 'department') and appointment.department:
                    print(f"DepartmentName: {appointment.department.DepartmentName}")
                if hasattr(appointment, 'patient_a') and appointment.patient_a:
                    patient = appointment.patient_a
                    print(f"Patient Full Name: {patient.FirstName} {patient.LastName}")
                if hasattr(appointment, 'practitioner_a') and appointment.practitioner_a:
                    print(f"Practitioner Full Name: {appointment.practitioner_a.FirstName}"
                          f" {appointment.practitioner_a.LastName}")
                print("---------------------")
            print(f"Total count of appointments that meet the search criteria: {total_count}")
        else:
            print("No appointments found for the given filtering criteria")

    # call all functions for receptionists
    elif operation == "add_receptionist":
        required_keys = ['EmployeeID', 'LastName', 'FirstName', 'DepartmentID']
        if all(key in json_dict for key in required_keys):
            if Reception.add_receptionist(session, json_dict):
                print("Success! The data was added to receptionists.")
            else:
                print("An error occurred while adding the data to receptionists.")
        else:
            print("Error. To add a new receptionist, please include EmployeeID, LastName,"
                  " FirstName, DepartmentID in your JSON object.")
    elif operation == "modify_receptionist":
        if Reception.modify_receptionist(session1, session2, json_dict, json_dict2):
            print("Success! The receptionists data was updated.")
        else:
            print("An error occurred while modifying the receptionists data. Please make sure to"
                  " specify the correct attribute names for modification.")
    elif operation == "delete_receptionist":
        if Reception.delete_receptionist(session1, session2, json_dict):
            print("Success! The data was deleted from receptionists.")
        else:
            print("An error occurred while deleting the data from receptionists. Please make sure to"
                  " specify the correct attribute names and values.")
    elif operation == "get_receptionist":
        if json_dict:
            receptionists, total_count = Reception.get_receptionist(session1, session2, json_dict)
        else:
            receptionists, total_count = Reception.get_receptionist(session1, session2)
        if receptionists:
            for row in receptionists:
                print("Receptionist:")
                for column in Reception.__table__.columns:
                    print(f"{column.name}: {getattr(row, column.name)}")
                if hasattr(row, 'department_r') and row.department_r:
                    print(f"DepartmentName: {row.department_r.DepartmentName}")
                print("---------------------")
            print(f"Total count of receptionists that meet the search criteria: {total_count}")
        else:
            print("No receptionists found")

    # call all practitioner functions
    elif operation == "add_practitioner":
        required_keys = ['EmployeeID', 'LastName', 'FirstName', 'LicenseNumber', 'Title',
                         'DepartmentID', 'Specialty']
        if all(key in json_dict for key in required_keys):
            if Practitioner.add_practitioner(session, json_dict):
                print("Success! The data was added to practitioners.")
            else:
                print("An error occurred while adding data to practitioners.")
        else:
            print("Error. To add a new practitioner, please include EmployeeID, LastName,"
                  " FirstName, LicenceNumber, Title, DepartmentID, and Specialty in your JSON object.")
    elif operation == "modify_practitioner":
        if Practitioner.modify_practitioner(session1, session2, json_dict, json_dict2):
            print("Success! The practitioner data was updated.")
        else:
            print("An error occurred while modifying the practitioner data. Please make sure to"
                  " specify the correct attribute names and values for modification.")
    elif operation == "delete_practitioner":
        if Practitioner.delete_practitioner(session1, session2, json_dict):
            print("Success! The practitioner data was deleted.")
        else:
            print("An error occurred while deleting the practitioner data. Please make sure to"
                  " specify the correct attribute names and values.")
    elif operation == "get_practitioner":
        if json_dict:
            practitioners, total_count = Practitioner.get_practitioner(session1, session2, json_dict)
        else:
            practitioners, total_count = Practitioner.get_practitioner(session1, session2)
        if practitioners:
            for row in practitioners:
                print("Practitioner:")
                for column in Practitioner.__table__.columns:
                    print(f"{column.name}: {getattr(row, column.name)}")
                if hasattr(row, 'department_p') and row.department_p:
                    print(f"DepartmentName: {row.department_p.DepartmentName}")
                print("---------------------")
            print(f"Total count of practitioners that meet the search criteria: {total_count}")
        else:
            print("No practitioners found")

    # call all functions for patients table
    elif operation == "add_patient":
        required_keys = ['PatientID', 'LastName', 'FirstName', 'DOB', 'Gender',
                         'Insurance', 'PastProcedures',
                         'Notes', 'DepartmentID']
        if all(key in json_dict for key in required_keys):
            if Patient.add_patient(session, json_dict):
                print("Success! The data was added to patients.")
            else:
                print("An error occurred while adding the data to patients.")
        else:
            print("Error. To add a new patient, please include PatientID, LastName, FirstName,"
                  " DepartmentID, Insurance, PastProcedures, and Notes in your JSON object.")
    elif operation == "modify_patient":
        if Patient.modify_patient(session1, session2, json_dict, json_dict2):
            print("Success! The patients data was updated.")
        else:
            print("An error occurred while modifying the patients data. Please make sure to"
                  " specify the correct attribute names and values for modification.")
    elif operation == "delete_patient":
        if Patient.delete_patient(session1, session2, json_dict):
            print("Success! The patients data was deleted.")
        else:
            print("An error occurred while deleting the patients data. Please make sure to"
                  " specify the correct attribute names and values.")
    elif operation == "get_patient":
        if json_dict:
            patients, total_count = Patient.get_patient(session1, session2, json_dict)
        else:
            patients, total_count = Patient.get_patient(session1, session2)
        if patients:
            patients.sort(key=lambda x: (x.DepartmentID, x.PatientID))
            for (dept_id, pat_id), group in itertools\
                    .groupby(patients, key=lambda x: (x.DepartmentID, x.PatientID)):
                print("Patient:")
                print(f"Department ID: {dept_id}, Patient ID: {pat_id}")
                for row in group:
                    for column in Patient.__table__.columns:
                        if column.name == "DepartmentID" or column.name == "PatientID":
                            continue
                        print(f"{column.name}: {getattr(row, column.name)}")
                    if hasattr(row, 'department_pa') and row.department_pa:
                        print(f"DepartmentName: {row.department_pa.DepartmentName}")
                    print("---------------------")
            print(f"Total count of patients that meet the search criteria: {total_count}")
        else:
            print("No patients found")

    # call patient of view/retrieve functions
    elif operation == "get_practitioners_for":
        if attribute_list:
            practitioners, total_count = PatientOf.get_practitioners_for(session1, session2, id_var, attribute_list)
        else:
            practitioners, total_count = PatientOf.get_practitioners_for(session1, session2, id_var)

        if practitioners:
            patient_name = session1.query(Patient.FirstName, Patient.LastName) \
                .join(PatientOf) \
                .join(Practitioner) \
                .filter(Patient.PatientID == id_var) \
                .first()
            if not patient_name:
                patient_name = session2.query(Patient.FirstName, Patient.LastName) \
                    .join(PatientOf) \
                    .join(Practitioner) \
                    .filter(Patient.PatientID == id_var) \
                    .first()

            first_name, last_name = patient_name
            print(f"Associated Practitioners for Patient {last_name}, {first_name}:")
            for patient_of_instance, practitioner_list in practitioners:
                for practitioner in practitioner_list:
                    if isinstance(practitioner, dict):  # If it's a dictionary
                        for key, value in practitioner.items():
                            print(f"{key}: {value}")
                        print("----------------------")
                    else:
                        practitioner_data = [(key, value) for key, value in practitioner.__dict__.items() if
                                            key != '_sa_instance_state']
                        for key, value in practitioner_data:
                            print(f"{key}: {value}")
                        print("----------------------")
            print(f"Total count of practitioners: {total_count}")
        else:
            print("No practitioners found for this patient. Please make sure to include the correct PatientID."
                  " If you wish to specify which columns to return, make sure provide the correct attribute"
                  " names in a list separated by ', '.")

    elif operation == "get_patients_of":
        if attribute_list:
            patients, total_count = PatientOf.get_patients_of(session1, session2, id_var, attribute_list)
        else:
            patients, total_count = PatientOf.get_patients_of(session1, session2, id_var)

        if patients:
            practitioner_name = session1.query(Practitioner.FirstName, Practitioner.LastName) \
                .filter_by(EmployeeID=id_var).first()
            if not practitioner_name:
                practitioner_name = session2.query(Practitioner.FirstName, Practitioner.LastName) \
                    .filter_by(EmployeeID=id_var).first()
            first_name = str(practitioner_name[0])
            last_name = str(practitioner_name[1])
            print(f"Associated Patients for Practitioner {last_name}, {first_name}:")

            for patient_of_instance, patients_list in patients:
                for patient in patients_list:
                    if isinstance(patient, dict):  # If it's a dictionary
                        for key, value in patient.items():
                            print(f"{key}: {value}")
                        print("----------------------")
                    else:
                        patient_data = [(key, value) for key, value in patient.__dict__.items() if
                                        key != '_sa_instance_state']
                        for key, value in patient_data:
                            print(f"{key}: {value}")
                        print("----------------------")
            print(f"Total count of patients: {total_count}")
        else:
            print("No patients found for this practitioner. Please make sure to include the correct PractitionerID."
                  " If you wish to specify which columns to return, make sure provide the correct attribute"
                  " names in a list separated by ', '.")

    else: # if no operation is called
        print("Error. Please make sure to use a valid operation name.")

    # closing sessions
    if session:
        if 'session' in locals() or 'session' in globals():  # closing the session
            session.close()
    if session1 or session2:
        if 'session1' in locals() or 'session1' in globals():
            # closing the double session
            session1.close()
            session2.close()


if __name__ == "__main__":
    main()
