-- ============================================
-- Job Market Intelligence — Core SQL Analysis
-- ============================================

-- 1. Total jobs by search term
SELECT search_term, COUNT(*) AS total_jobs
FROM jobs_raw
GROUP BY search_term
ORDER BY total_jobs DESC;

-- 2. Average salary by seniority level
SELECT seniority,
       COUNT(*) AS total,
       ROUND(AVG(salary_avg)::numeric, 2) AS avg_salary,
       ROUND(MIN(salary_avg)::numeric, 2) AS min_salary,
       ROUND(MAX(salary_avg)::numeric, 2) AS max_salary
FROM jobs_raw
WHERE salary_avg > 0
GROUP BY seniority
ORDER BY avg_salary DESC;

-- 3. Top 10 hiring companies
SELECT company, COUNT(*) AS job_count
FROM jobs_raw
GROUP BY company
ORDER BY job_count DESC
LIMIT 10;

-- 4. Remote vs onsite breakdown
SELECT is_remote,
       COUNT(*) AS total,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM jobs_raw
GROUP BY is_remote;

-- 5. Top 10 locations
SELECT location, COUNT(*) AS job_count
FROM jobs_raw
WHERE location IS NOT NULL
GROUP BY location
ORDER BY job_count DESC
LIMIT 10;

-- 6. Salary distribution by search term
SELECT search_term,
       ROUND(AVG(salary_avg)::numeric, 2) AS avg_salary,
       COUNT(*) AS jobs_with_salary
FROM jobs_raw
WHERE salary_avg > 0
GROUP BY search_term
ORDER BY avg_salary DESC;

-- 7. Jobs posted by date
SELECT created_date, COUNT(*) AS jobs_posted
FROM jobs_raw
WHERE created_date IS NOT NULL
GROUP BY created_date
ORDER BY created_date DESC
LIMIT 14;

-- 8. Seniority breakdown per search term
SELECT search_term, seniority, COUNT(*) AS total
FROM jobs_raw
GROUP BY search_term, seniority
ORDER BY search_term, total DESC;