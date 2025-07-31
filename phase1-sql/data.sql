use lib_mng_system;

insert into Libraries values
(1, 'Central Library', 'Main Campus', 'central@univ.edu', '9876543210'),
(2, 'Science Library', 'Science Block', 'science@univ.edu', '9876543211'),
(3, 'Arts Library', 'Arts Block', 'arts@univ.edu', '9876543212');

insert into Book values
(1, 1, 'The Great Gatsby', '1234567890123', '1925-04-10', 5, 3),
(2, 1, 'Pride and Prejudice', '1234567890124', '1813-01-28', 4, 4),
(3, 1, 'Adventures of Huckleberry Finn', '1234567890125', '1884-12-10', 6, 5),
(4, 1, 'Wuthering Heights', '1234567890126', '1847-12-01', 3, 1),
(5, 2, 'Modern Computing', '1234567890127', '2010-05-10', 7, 6),
(6, 2, 'Relativity Theory', '1234567890128', '1916-01-01', 4, 2),
(7, 2, 'Radioactivity Basics', '1234567890129', '1906-11-05', 3, 1),
(8, 2, 'Newtonian Mechanics', '1234567890130', '1687-07-05', 4, 2),
(9, 2, 'Data Structures', '1234567890131', '2015-08-20', 6, 5),
(10, 3, 'Indian History', '1234567890132', '1990-01-15', 5, 3),
(11, 3, 'Western Philosophy', '1234567890133', '1980-03-10', 3, 2),
(12, 3, 'Machine Learning Basics', '1234567890134', '2020-09-01', 8, 7),
(13, 3, 'The Future of AI', '1234567890135', '2021-10-15', 6, 6),
(14, 3, 'Ethics and Morality', '1234567890136', '2000-06-25', 2, 1),
(15, 3, 'Cosmos', '1234567890137', '1980-09-01', 4, 3);

insert into Author values
(1, 'John', 'Doe', '1970-05-12', 'American', 'Expert in literature.'),
(2, 'Jane', 'Austen', '1985-11-20', 'British', 'Known for romance novels.'),
(3, 'Mark', 'Twain', '1965-03-15', 'American', 'Humorist and writer.'),
(4, 'Emily', 'Bronte', '1978-07-30', 'British', 'Author of Wuthering Heights.'),
(5, 'Ravi', 'Shankar', '1980-01-01', 'Indian', 'Writes about modern computing.'),
(6, 'Albert', 'Einstein', '1955-03-14', 'German', 'Physics and relativity.'),
(7, 'Marie', 'Curie', '1867-11-07', 'Polish', 'Pioneer in radioactivity.'),
(8, 'Isaac', 'Newton', '1643-01-04', 'British', 'Gravity and motion.');

insert into Category values
(1, 'Fiction', 'Novels and literary works'),
(2, 'Science', 'Books related to science and research'),
(3, 'History', 'Historical accounts and research'),
(4, 'Technology', 'Computers and technology'),
(5, 'Philosophy', 'Books on human thought and logic');

insert into Member (first_name, last_name, email, phone, member_type, registration_date) values
('Amit', 'Kumar', 'amit@student.edu', '9876500001', 'student', '2023-01-10'),
('Sara', 'Ali', 'sara@faculty.edu', '9876500002', 'faculty', '2022-12-15'),
('Raj', 'Singh', 'raj@student.edu', '9876500003', 'student', '2023-02-20'),
('Priya', 'Verma', 'priya@faculty.edu', '9876500004', 'faculty', '2022-11-05'),
('John', 'Smith', 'john@student.edu', '9876500005', 'student', '2023-03-01'),
('Emily', 'Stone', 'emily@faculty.edu', '9876500006', 'faculty', '2023-01-30'),
('Neha', 'Sharma', 'neha@student.edu', '9876500007', 'student', '2023-03-15'),
('Aarav', 'Patel', 'aarav@student.edu', '9876500008', 'student', '2023-04-10'),
('Reena', 'Gupta', 'reena@faculty.edu', '9876500009', 'faculty', '2022-10-01'),
('Mohit', 'Jain', 'mohit@student.edu', '9876500010', 'student', '2023-02-05'),
('Anjali', 'Mishra', 'anjali@student.edu', '9876500011', 'student', '2023-01-22'),
('Karan', 'Malhotra', 'karan@student.edu', '9876500012', 'student', '2023-03-28'),
('Deepa', 'Joshi', 'deepa@faculty.edu', '9876500013', 'faculty', '2022-09-12'),
('Sunny', 'Deol', 'sunny@student.edu', '9876500014', 'student', '2023-04-01'),
('Lata', 'Rani', 'lata@student.edu', '9876500015', 'student', '2023-03-18'),
('Manoj', 'Tiwari', 'manoj@faculty.edu', '9876500016', 'faculty', '2022-08-25'),
('Geeta', 'Sharma', 'geeta@student.edu', '9876500017', 'student', '2023-05-02'),
('Abhay', 'Yadav', 'abhay@student.edu', '9876500018', 'student', '2023-06-10'),
('Divya', 'Pandey', 'divya@student.edu', '9876500019', 'student', '2023-06-18'),
('Tarun', 'Raj', 'tarun@faculty.edu', '9876500020', 'faculty', '2022-07-30');

insert into Borrowing (member_id, book_id, borrow_date, due_date, return_date, late_fee) values
(1, 1, '2024-06-01', '2024-06-15', '2024-06-14', 0),
(2, 2, '2024-06-03', '2024-06-17', '2024-06-20', 10),
(3, 3, '2024-06-05', '2024-06-20', '2024-06-18', 0),
(4, 4, '2024-06-07', '2024-06-21', null, 0),
(5, 5, '2024-06-09', '2024-06-23', '2024-06-25', 5),
(6, 6, '2024-06-10', '2024-06-24', null, 0),
(7, 7, '2024-06-11', '2024-06-25', '2024-06-26', 2),
(8, 8, '2024-06-12', '2024-06-26', null, 0),
(9, 9, '2024-06-13', '2024-06-27', '2024-06-27', 0),
(10, 10, '2024-06-14', '2024-06-28', null, 0),
(11, 11, '2024-06-15', '2024-06-29', null, 0),
(12, 12, '2024-06-16', '2024-06-30', '2024-06-30', 0),
(13, 13, '2024-06-17', '2024-07-01', null, 0),
(14, 14, '2024-06-18', '2024-07-02', null, 0),
(15, 15, '2024-06-19', '2024-07-03', null, 0),
(16, 1, '2024-06-20', '2024-07-04', null, 0),
(17, 2, '2024-06-21', '2024-07-05', null, 0),
(18, 3, '2024-06-22', '2024-07-06', null, 0),
(19, 4, '2024-06-23', '2024-07-07', null, 0),
(20, 5, '2024-06-24', '2024-07-08', null, 0),
(1, 6, '2024-06-25', '2024-07-09', null, 0),
(2, 7, '2024-06-26', '2024-07-10', null, 0),
(3, 8, '2024-06-27', '2024-07-11', null, 0),
(4, 9, '2024-06-28', '2024-07-12', null, 0),
(5, 10, '2024-06-29', '2024-07-13', null, 0);

insert into Review (member_id, book_id, rating, comment, review_date) values
(1, 1, 4.5, 'Excellent read!', '2024-06-15'),
(2, 2, 4.0, 'Classic literature.', '2024-06-16'),
(3, 3, 3.5, 'Enjoyed the humor.', '2024-06-17'),
(4, 4, 5.0, 'Masterpiece!', '2024-06-18'),
(5, 5, 4.2, 'Very informative.', '2024-06-19'),
(6, 6, 4.8, 'Highly recommended.', '2024-06-20'),
(7, 7, 3.8, 'Good for beginners.', '2024-06-21'),
(8, 8, 4.1, 'Well explained concepts.', '2024-06-22'),
(9, 9, 4.6, 'Great for CS students.', '2024-06-23'),
(10, 10, 4.0, 'Nice historical coverage.', '2024-06-24'),
(11, 11, 3.9, 'Thought-provoking.', '2024-06-25'),
(12, 12, 4.3, 'Excellent for ML intro.', '2024-06-26');

insert into BookAuthor values
(1, 1),
(2, 2),
(3, 3),
(4, 4),
(5, 5),
(6, 6),
(7, 7),
(8, 8),
(9, 5),
(10, 1),
(11, 2),
(12, 5),
(13, 5),
(14, 4),
(15, 6);

insert into BookCategory values
(1, 1),
(2, 1),
(3, 1),
(4, 1),
(5, 4),
(6, 2),
(7, 2),
(8, 2),
(9, 4),
(10, 3),
(11, 5),
(12, 4),
(13, 4),
(14, 5),
(15, 2);

