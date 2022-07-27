import logging
import os
import sys
import datetime
import traceback

from django.db import transaction

from sql.models import ExportEnvWorkflow

logger = logging.getLogger('default')

'''
导出脚本 
date: 从传入时间起开始导出脚本
'''
def export_sqlscripts(env_id, env_name, version, sqlWorkflowContentArr, firstExport):
    # 生成文件夹名
    folder_name = env_name + '_' + version + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    # 生成压缩包名
    zip_name = folder_name + '.tar.gz '
    num = 0
    os.chdir('/data/scripts/')
    isExists = os.path.exists(folder_name)
    if not isExists:
        os.mkdir(folder_name)
    else:
        pass
    os.chdir(folder_name)
    try:
        for row in sqlWorkflowContentArr:
            sql_content = row.sql_content
            db_name = row.workflow.db_name
            if env_name == 'demo':
                db_name = db_name+'_'+env_name
                sql_content = sql_content.replace("ksp_admindb", "ksp_admindb_demo")
                sql_content = sql_content.replace("ksp_authdb", "ksp_authdb_demo")
                sql_content = sql_content.replace("ksp_cateringdb", "ksp_cateringdb_demo")
                sql_content = sql_content.replace("ksp_demodb", "ksp_demodb_demo")
                sql_content = sql_content.replace("ksp_developerdb", "ksp_developerdb_demo")
                sql_content = sql_content.replace("ksp_hoteldb", "ksp_hoteldb_demo")
                sql_content = sql_content.replace("ksp_marketingdb", "ksp_marketingdb_demo")
                sql_content = sql_content.replace("ksp_merchantdb", "ksp_merchantdb_demo")
                sql_content = sql_content.replace("ksp_restaurantdb", "ksp_restaurantdb_demo")
                sql_content = sql_content.replace("ksp_retaildb", "ksp_retaildb_demo")
                sql_content = sql_content.replace("ksp_scenicdb", "ksp_scenicdb_demo")
                sql_content = sql_content.replace("xxl_job", "xxl_job_demo")
            output(version, row.workflow.engineer, row.workflow.create_time, sql_content, db_name)
            num=num+1
            if firstExport == 'true':
                with transaction.atomic():
                    # 保存申请信息到数据库
                    exportEnvWorkflow = ExportEnvWorkflow(
                        env_id=env_id,
                        workflow_id=row.workflow.id
                    )
                    exportEnvWorkflow.save()
    except Exception as e:
        logger.error(traceback.format_exc())
    os.chdir('../')
    os.system('tar -czf ' + zip_name + ' ' + folder_name + ' --remove-files')
    os.system('ossutil64 cp '+zip_name+'oss://sdp-metadata/sqlscripts/ebase/')
    return zip_name

'''
写入文本 
title: 文件名
author: 作者
date: 提交时间
sql: sql
'''
def output(version, author, date, sql, db_name):
    file_name = str(version)+'_'+str(date.strftime("%Y-%m-%d_%H:%M:%S"))+'_'+str(author)+'.sql'
    try:
        file = open(file_name, 'a', encoding='utf-8')
        file.write("use "+str(db_name)+";\r\n")
        execsql = str(sql)
        file.write(execsql)
        print(str(file_name)+'写入完成!')
    except IOError as ex:
        print(ex)
        print(str(file_name)+'写入时发生错误!')
    finally:
        file.close()
