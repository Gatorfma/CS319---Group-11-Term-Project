-- init.sql
-- Run this against your django_db to create initial users.
-- All passwords are "password123".

USE django_db;

INSERT INTO accounts_customuser
  (password, last_login, is_superuser, username, first_name, last_name, email,
   is_staff, is_active, date_joined, role, employee_id, department, phone_number)
VALUES
  /* Super‐admin */
  (
    'pbkdf2_sha256$260000$1L0G4VfGXCaM$X0oiiZ8dYWymT9UO+tV5G9wlUkM27FaaENzhJ6g6Jr4=',
    NULL, 1, 'admin', 'Admin', 'User', 'admin@example.com',
    1, 1, NOW(), 'ADMIN',      'EMP000', 'Administration',  '555-0001'
  ),
  /* Teaching Assistant */
  (
    'pbkdf2_sha256$260000$1L0G4VfGXCaM$X0oiiZ8dYWymT9UO+tV5G9wlUkM27FaaENzhJ6g6Jr4=',
    NULL, 0, 'ta_jane', 'Jane', 'TA', 'jane.ta@example.com',
    0, 1, NOW(), 'TA',         'EMP101', 'Computer Science','555-0101'
  ),
  /* Instructor */
  (
    'pbkdf2_sha256$260000$1L0G4VfGXCaM$X0oiiZ8dYWymT9UO+tV5G9wlUkM27FaaENzhJ6g6Jr4=',
    NULL, 0, 'instr_bob', 'Bob', 'Instructor', 'bob.instr@example.com',
    0, 1, NOW(), 'INSTRUCTOR','EMP201', 'Mathematics',     '555-0202'
  ),
  /* Secretary */
  (
    'pbkdf2_sha256$260000$1L0G4VfGXCaM$X0oiiZ8dYWymT9UO+tV5G9wlUkM27FaaENzhJ6g6Jr4=',
    NULL, 0, 'sec_sara', 'Sara', 'Secretary', 'sara.sec@example.com',
    1, 1, NOW(), 'SECRETARY', 'EMP301', 'Admin Office',    '555-0303'
  ),
  /* Department Chair */
  (
    'pbkdf2_sha256$260000$1L0G4VfGXCaM$X0oiiZ8dYWymT9UO+tV5G9wlUkM27FaaENzhJ6g6Jr4=',
    NULL, 0, 'chair_tim', 'Tim', 'Chair', 'tim.chair@example.com',
    1, 1, NOW(), 'DEPT_CHAIR','EMP401', 'Physics',          '555-0404'
  ),
  /* Dean */
  (
    'pbkdf2_sha256$260000$1L0G4VfGXCaM$X0oiiZ8dYWymT9UO+tV5G9wlUkM27FaaENzhJ6g6Jr4=',
    NULL, 0, 'dean_lucy', 'Lucy', 'Dean', 'lucy.dean@example.com',
    1, 1, NOW(), 'DEAN',       'EMP501', 'Dean Office',     '555-0505'
  );
