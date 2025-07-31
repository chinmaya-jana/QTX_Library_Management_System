use lib_mng_system;

-- Extra Question:
select * from author;
select * from book;
select * from bookauthor;
select * from category;
select * from bookcategory;
select * from borrowing;
select * from libraries;
select * from member;
select * from review;

-- Complex Query Operations: Write queries to demonstrate:

-- JOIN operations across multiple tables
-- Aggregation functions (COUNT, AVG, SUM)
-- Subqueries and Common Table Expressions (CTEs)
-- Window functions
-- Transaction management

-- Q01. find the number of books written by any author
select ba.author_id, 
	concat(a.first_name, " ", a.last_name) as Author_Name, 
    count(b.book_id) as total_written_books
from bookauthor as ba
join author as a
on ba.author_id = a.author_id
join book as b
on ba.book_id = b.book_id
group by ba.author_id;

-- Q2. Find the number of books in available in each library.
with books_in_lib as (
	select library_id, 
		sum(available_copies) as total_books
	from book
	group by library_id
	)
select l.library_id,
	l.name,
    bl.total_books
from books_in_lib as bl
left join libraries as l
on bl.library_id = l.library_id;

-- Q03. Total number of books borrow by a member with fine
select * from borrowing;
select * from member;
with borrow as (
	select member_id, 
		count(book_id) as total_borrow_book,
		sum(late_fee) as fine
	from borrowing
	group by member_id
	)
select m.member_id,
	concat(m.first_name, " ", last_name) as Name,
    total_borrow_book,
    fine
from borrow as b
right join member as m
on b.member_id = m.member_id;

-- Q4. Check the status of borrow
select * from borrowing;
select member_id,
	case 
		when return_date is not null then "Returned" 
        else "due"
	end as "Status"
from borrowing;