-- DDL
-- 1. Create database "Library Management System"
create database if not exists lib_mng_system;

-- 2. Use that database
use lib_mng_system;

-- 3. Create Tables
-- i. Table 1: Libraries
create table if not exists Libraries (
library_id int primary key,
name varchar(50) not null,
campus_location varchar(100),
contact_email varchar(100) not null,
phone_number varchar(10)
);

-- ii. Table 2: Book
create table if not exists book (
book_id int primary key,
library_id int,
title varchar(100),
isbn char(13) unique,
publication_date date,
total_copies int,
available_copies int,
foreign key (library_id) references libraries(library_id)
);

alter table book
add constraint chk_available_less_than_total
check (available_copies <= total_copies);

-- iii. Table 3: Author
create table if not exists Author (
author_id int primary key,
first_name varchar(50) not null,
last_name varchar(50) not null,
birth_date date,
nationality varchar(50),
biography varchar(200)
);

-- iv. Table 4: Category
create table if not exists Category (
category_id int primary key,
name varchar(50),
description varchar(100)
);

-- v. Table 5: Member
create table if not exists Member (
member_id int auto_increment primary key,
first_name varchar(50),
last_name varchar(50),
email varchar(50),
phone char(10),
member_type varchar(10),
registration_date date,
check (member_type in('student','faculty'))
);

-- vi. Table 6: Borrowing
create table if not exists Borrowing (
borrowing_id int auto_increment primary key,
member_id int,
book_id int,
borrow_date date not null,
due_date date,
return_date date,
late_fee float,
foreign key (member_id) references member(member_id),
foreign key (book_id) references book(book_id),
check (due_date > borrow_date)
);

-- vii. Table 7: Review
create table if not exists Review (
review_id int auto_increment primary key,
member_id int,
book_id int,
rating float,
comment varchar(200),
review_date date not null,
foreign key (member_id) references Member(member_id),
foreign key (book_id) references Book(book_id),
check (rating between 1 and 5)
);

-- viii. Table 8: BookAuthor
create table if not exists BookAuthor (
book_id int,
author_id int,
primary key(book_id, author_id),
foreign key (book_id) references Book(book_id),
foreign key (author_id) references Author(author_id)
);

-- ix. Table 9: BookCategory
create table if not exists BookCategory (
book_id int,
category_id int,
primary key(book_id, category_id),
foreign key (book_id) references Book(book_id),
foreign key (category_id) references Category(category_id)
);
