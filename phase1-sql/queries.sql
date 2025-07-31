-- DQL
SELECT * FROM LIBRARIES;
select * from book;
SELECT * FROM AUTHOR;
select * from Category;
SELECT * FROM MEMBER;
select * from borrowing;
SELECT * FROM REVIEW;
select * from bookauthor;
SELECT * FROM BOOKCATEGORY;

-- Q1. Books with their authors and categories
select b.isbn as ISBN,
    b.title as Book_Title,
    concat(a.first_name, " ", a.last_name) as Author,
    c.name as Category,
    c.description
from bookauthor as ba
join book as b
on ba.book_id = b.book_id
join author as a
on ba.author_id = a.author_id
join bookcategory as bc
on b.book_id = bc.book_id
join category as c
on c.category_id = bc.category_id;

-- Q2. Most borrowed books in the last 30 days

-- Note: I inserted data between '2024-06-01' and '2024-06-29'
-- Note: That's why I pick the last 20 days of that month (June 2024) 
with most_borrowed_books as (
	select book_id, count(book_id) as borrowing_times from borrowing
	where borrow_date between '2024-06-10' and '2024-06-30' 
	group by book_id
	order by borrowing_times desc
	)
select b.book_id as book_id,
	b.isbn as ISBN,
	b.title as book_title,
    mbb.borrowing_times as most_borrow,
    dense_rank() over(order by mbb.borrowing_times desc) as 'Priority'
from book as b
join most_borrowed_books as mbb
on b.book_id = mbb.book_id;

-- Q3. Members with overdue books and calculated late fees
select * from member;
select * from borrowing;
select m.member_id,
	concat(first_name, " ", last_name) as Name,
    email,
    phone,
    member_type,
	sum(late_fee) as fine
from borrowing as b
join member as m
on b.member_id = m.member_id
where late_fee > 0
group by member_id;

-- Q4. Average rating per book with author information
with avg_book_rating as (
	select book_id, 
		avg(rating) as avg_rating 
	from review
	group by book_id 
	)
select ba.book_id, 
	b.isbn as ISBN, 
	b.title as book_title, 
	ba.author_id, 
	concat(a.first_name, " ", a.last_name) as Author,
	abr.avg_rating as avg_rating
from bookauthor as ba
join book as b
on ba.book_id = b.book_id
join author as a
on ba.author_id = a.author_id
join avg_book_rating as abr
on b.book_id = abr.book_id
order by avg_rating desc; -- this lines add more information

-- 5. Books available in each library with stock levels
select book_id, 
	l.library_id, 
    l.name as library_name, 
    available_copies
from book as b
join libraries as l
on b.library_id = l.library_id;
