-- PrintFlow reporting queries - PostgreSQL / SQLite-compatible syntax
-- 1 Pending jobs
SELECT job_number,title,status,quantity,delivered_qty FROM jobs WHERE status <> 'DELIVERED';
-- 2 Material issues / usage
SELECT j.job_number,m.name,SUM(i.quantity) AS used_quantity FROM material_issues i JOIN jobs j ON j.id=i.job_id JOIN materials m ON m.id=i.material_id GROUP BY j.job_number,m.name;
-- 3 Machine schedule / load
SELECT m.name,s.start_at,s.end_at,j.job_number FROM schedules s JOIN machines m ON m.id=s.machine_id JOIN jobs j ON j.id=s.job_id ORDER BY m.name,s.start_at;
-- 4 Production stage progress
SELECT j.job_number,st.stage_name,st.status FROM stages st JOIN jobs j ON j.id=st.job_id ORDER BY j.id,st.id;
-- 5 Delivery balance
SELECT job_number,quantity,delivered_qty,(quantity-delivered_qty) AS pending_delivery FROM jobs;
-- 6 Revenue
SELECT COALESCE(SUM(amount),0) AS payments_received FROM payments;
-- 7 Invoice balance
SELECT i.id,i.job_id,i.total,COALESCE(SUM(p.amount),0) AS paid,i.total-COALESCE(SUM(p.amount),0) AS balance FROM invoices i LEFT JOIN payments p ON p.invoice_id=i.id GROUP BY i.id,i.job_id,i.total;
-- 8 Low stock
SELECT name,stock,reorder_level,unit FROM materials WHERE stock<=reorder_level;
-- 9 Material spending (simplified usage-cost estimate)
SELECT i.job_id,SUM(i.quantity*m.unit_cost) AS material_cost FROM material_issues i JOIN materials m ON m.id=i.material_id GROUP BY i.job_id;
