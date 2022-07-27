import datetime
import json
import logging
import traceback

from django.db.models import Q
from django.utils import timezone

from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.http import HttpResponse

from common.utils.extend_json_encoder import ExtendJSONEncoder
from sql.models import ExportEnv, SqlWorkflow, ExportEnvWorkflow, SqlWorkflowContent
from sql.utils.export_sql import output, export_sqlscripts
from sql.utils.resource_group import user_groups

logger = logging.getLogger('default')

@permission_required('sql.export_env_commit', raise_exception=True)
def commit(request):
    """
    提交新增导出环境
    :param request:
    :return:
    """
    name = request.POST['name']
    remarks = request.POST.get('remarks')

    # 获取用户信息
    user = request.user

    # 服务端参数校验
    result = {'status': 0, 'msg': 'ok', 'data': []}

    # 使用事务保持数据一致性
    try:
        with transaction.atomic():
            # 保存申请信息到数据库
            exportenv = ExportEnv(
                name=name,
                remarks=remarks,
                create_user=user.id,
                create_time=timezone.now()
            )
            exportenv.save()
    except Exception as msg:
        logger.error(traceback.format_exc())
        result['status'] = 1
        result['msg'] = str(msg)
    return HttpResponse(json.dumps(result), content_type='application/json')


@permission_required('sql.export_workflow_list', raise_exception=True)
def notexport_workflow_list(request):
    """
    获取未导出列表
    :param request:
    :return:
    """
    nav_status = request.POST.get('navStatus')
    instance_id = request.POST.get('instance_id')
    resource_group_id = request.POST.get('group_id')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    env = request.POST.get('env')
    search = request.POST.get('search')
    user = request.user
    rows = []
    count = 0
    if env != '':
        # 组合筛选项
        filter_dict = dict()
        # 工单状态
        if nav_status:
            filter_dict['status'] = nav_status
        # 实例
        if instance_id:
            filter_dict['instance_id'] = instance_id
        # 资源组
        if resource_group_id:
            filter_dict['group_id'] = resource_group_id
        # 时间
        if start_date and end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            filter_dict['create_time__range'] = (start_date, end_date)
        # 管理员，可查看所有工单
        if user.is_superuser:
            pass
        # 非管理员，拥有审核权限、资源组粒度执行权限的，可以查看组内所有工单
        elif user.has_perm('sql.sql_review') or user.has_perm('sql.sql_execute_for_resource_group'):
            # 先获取用户所在资源组列表
            group_list = user_groups(user)
            group_ids = [group.group_id for group in group_list]
            filter_dict['group_id__in'] = group_ids
        # 其他人只能查看自己提交的工单
        else:
            filter_dict['engineer'] = user.username
        # 过滤组合筛选项
        workflow = SqlWorkflow.objects.filter(**filter_dict)
        env_dict = dict()
        workflow_arr = []
        logger.info(f'环境为：{env}')
        env_dict['env_id'] = env
        exportEnvWorkflow = ExportEnvWorkflow.objects.filter(**env_dict).values("env_id", "workflow_id")
        for envWorkflow in exportEnvWorkflow:
            workflow_arr.append(envWorkflow.get('workflow_id'))
        # 未导出的SQL工单
        workflow = workflow.exclude(Q(pk__in=workflow_arr))
        # 过滤搜索项，模糊检索项包括提交人名称、工单名
        if search:
            workflow = workflow.filter(Q(engineer_display__icontains=search) | Q(workflow_name__icontains=search))

        count = workflow.count()
        workflow_list = workflow.order_by('-create_time').values(
            "id", "workflow_name", "engineer_display",
            "status", "is_backup", "create_time",
            "instance__instance_name", "db_name",
            "group_name", "syntax_type")
        # QuerySet 序列化
        rows = [row for row in workflow_list]
    result = {"total": count, "rows": rows}
    # 返回查询结果
    return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder, bigint_as_string=True),
                        content_type='application/json')

@permission_required('sql.export_workflow_list', raise_exception=True)
def export_workflow_list(request):
    """
    获取已导出列表
    :param request:
    :return:
    """
    nav_status = request.POST.get('navStatus')
    instance_id = request.POST.get('instance_id')
    resource_group_id = request.POST.get('group_id')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    env = request.POST.get('env')
    search = request.POST.get('search')
    user = request.user
    rows = []
    count = 0
    if env != '':
        # 组合筛选项
        filter_dict = dict()
        # 工单状态
        if nav_status:
            filter_dict['status'] = nav_status
        # 实例
        if instance_id:
            filter_dict['instance_id'] = instance_id
        # 资源组
        if resource_group_id:
            filter_dict['group_id'] = resource_group_id
        # 时间
        if start_date and end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            filter_dict['create_time__range'] = (start_date, end_date)
        # 管理员，可查看所有工单
        if user.is_superuser:
            pass
        # 非管理员，拥有审核权限、资源组粒度执行权限的，可以查看组内所有工单
        elif user.has_perm('sql.sql_review') or user.has_perm('sql.sql_execute_for_resource_group'):
            # 先获取用户所在资源组列表
            group_list = user_groups(user)
            group_ids = [group.group_id for group in group_list]
            filter_dict['group_id__in'] = group_ids
        # 其他人只能查看自己提交的工单
        else:
            filter_dict['engineer'] = user.username
        # 过滤组合筛选项
        workflow = SqlWorkflow.objects.filter(**filter_dict)

        env_dict = dict()
        workflow_arr = []
        logger.info(f'环境为：{env}')
        env_dict['env_id'] = env
        exportEnvWorkflow = ExportEnvWorkflow.objects.filter(**env_dict).values("env_id", "workflow_id")
        for envWorkflow in exportEnvWorkflow:
            workflow_arr.append(envWorkflow.get('workflow_id'))
        # 未导出的SQL工单
        workflow = workflow.filter(Q(pk__in=workflow_arr))
        # 过滤搜索项，模糊检索项包括提交人名称、工单名
        if search:
            workflow = workflow.filter(Q(engineer_display__icontains=search) | Q(workflow_name__icontains=search))

        count = workflow.count()
        workflow_list = workflow.order_by('-create_time').values(
            "id", "workflow_name", "engineer_display",
            "status", "is_backup", "create_time",
            "instance__instance_name", "db_name",
            "group_name", "syntax_type")

        # QuerySet 序列化
        rows = [row for row in workflow_list]
    result = {"total": count, "rows": rows}
    # 返回查询结果
    return HttpResponse(json.dumps(result, cls=ExtendJSONEncoder, bigint_as_string=True),
                        content_type='application/json')


@permission_required('sql.export_sql_export', raise_exception=True)
def export(request):
    """
    导出工单SQL
    :param request:
    :return:
    """
    ids = json.loads(request.POST.get('ids'))
    version = request.POST.get('versionName')
    env_id = request.POST.get('env_id')
    firstExport = request.POST.get('firstExport')
    logger.info(f'是否第一次导出：{firstExport}')
    try:
        exportEnv = ExportEnv.objects.get(id=env_id)
        sqlWorkflowContentArr = SqlWorkflowContent.objects.filter(workflow_id__in=ids)
        logger.info(f'工单明细：{sqlWorkflowContentArr[0].workflow.status}')
        zip_name = export_sqlscripts(env_id, exportEnv.name, version, sqlWorkflowContentArr, firstExport)
        result = {'status': 0, 'msg': f'导出成功，导出包名为： {zip_name}'}
    except Exception as e:
        logger.error(traceback.format_exc())
        result = {'status': 1, 'msg': str(e)}
    return HttpResponse(json.dumps(result), content_type='application/json')