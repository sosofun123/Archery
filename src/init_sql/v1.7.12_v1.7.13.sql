-- 增加权限
set @content_type_id=(select id from django_content_type where app_label='sql' and model='permission');
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('SQL工单转移资源组', @content_type_id, 'sql_workflow_change_group');

-- 新增导出环境表
DROP TABLE IF EXISTS export_env;
CREATE TABLE export_env (
id int(11) NOT NULL AUTO_INCREMENT,
name varchar(50),
remarks varchar(100),
create_user varchar(20) NOT NULL,
create_time datetime(6) NOT NULL,
PRIMARY KEY (`id`)
)ENGINE = InnoDB DEFAULT CHARSET = utf8 COMMENT = '导出环境';

-- 新增导出环境工单
DROP TABLE IF EXISTS export_env_workflow;
CREATE TABLE export_env_workflow (
env_id int(11),
workflow_id int(11)
)ENGINE = InnoDB DEFAULT CHARSET = utf8 COMMENT = '导出环境工单';


-- 增加权限
set @content_type_id=(select id from django_content_type where app_label='sql' and model='permission');
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('提交新增导出环境', @content_type_id, 'export_env_commit');
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('获取未导出/已导出列表', @content_type_id, 'export_workflow_list');
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('导出工单SQL', @content_type_id, 'export_sql_export');
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('菜单 SQL导出', @content_type_id, 'menu_sqlexport');