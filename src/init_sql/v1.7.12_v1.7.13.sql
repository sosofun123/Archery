-- 增加权限
set @content_type_id=(select id from django_content_type where app_label='sql' and model='permission');
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('SQL工单转移资源组', @content_type_id, 'sql_workflow_change_group');