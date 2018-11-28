from functools import wraps
import random
from flask import abort, flash
from flask_login import current_user
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from werkzeug.security import generate_password_hash


def list_gen(query, item):
    """查询结果列表生成（每一个列表项为一个相关键值的字符串）

    :param query: 查询语句
    :param item: 包括相关查询查询键值的字典字符串（需要eval进行转换，转换后则包括了obj）
    :return: 查询结果列表
    """

    list = []
    for obj in query:
        dict = eval(item)
        list.append(dict)
    return list


def dict_to_obj(dict, obj):
    """将字典转换成对象

    :param dict: 字典
    :param obj: 对象
    :return: 转换后的对象
    """

    for key in dict:
        setattr(obj, key, dict[key])
    return obj


def obj_to_dict(obj):
    """将对象转换成字典

    :param obj: 对象
    :return: 转换后的字典
    """

    dict = obj.__dict__['__data__']
    return dict


def form_to_model(form, model):
    """将wtf表单转换成model对象

    :param form: wtf表单
    :param model: 转换后的model对象
    :return: 无
    """

    for wtf in form:
        # 因为generate_password_hash方法创建的初始密码长度为10，因此长度等于10，表示是新建用户而非修改用户，才需生成
        if wtf.name == 'password' and len(wtf.data) == 10:
            flash('初始密码为 %s 。' % wtf.data)
            wtf.data = generate_password_hash(wtf.data)
        model.__setattr__(wtf.name, wtf.data)


def model_to_form(model, form):
    """将model对象转换成wtf表单

    :param model: model对象
    :param form: 转换后的wtf表单
    :return: 无
    """

    dict = obj_to_dict(model)
    form_key_list = [key for key in form.__dict__]
    for key, value in dict.items():
        if key in form_key_list and value:
            field = form.__getitem__(key)
            field.data = value
            form.__setattr__(key, field)


def flash_errors(form):
    """显示wtf表单错误信息

    :param form: wtf表单
    :return: 无
    """

    for field, errors in form.errors.items():
        for error in errors:
            flash("字段 [%s] 格式有误,错误原因: %s" % (getattr(form, field).label.text, error))


# 验证码生成
LOWER_LETTERS = "abcdefghjkmnpqrstuvwxy"  # 小写字母，去除可能干扰的i，l，o，z
UPPER_LETTERS = LOWER_LETTERS.upper()  # 大写字母
NUMBERS = ''.join(map(str, range(10)))  # 数字
INIT_CHARS = ''.join((LOWER_LETTERS, UPPER_LETTERS, NUMBERS))


def create_validate_code(size=(160, 24),
                         chars=INIT_CHARS,
                         mode="RGB",
                         bg_color=(230, 230, 230),
                         fg_color=(18, 18, 18),
                         font_size=15,
                         font_type='cronmon/static/fonts/msyhbd.ttf',
                         length=6,
                         draw_lines=True,
                         n_line=(1, 1),
                         draw_points=True,
                         point_chance=1):
    """生成验证码图片，图片格式为gif，使用微软雅黑粗体字体

    :param size: 图片的大小，格式（宽，高），默认为(120, 30)
    :param chars: 允许的字符集合，格式字符串
    :param img_type: 图片保存的格式，默认为GIF，可选的为GIF，JPEG，TIFF，PNG
    :param mode: 图片模式，默认为RGB
    :param bg_color: 背景颜色，默认为白色
    :param fg_color: 前景色，验证码字符颜色，默认为蓝色#0000FF
    :param font_size: 验证码字体大小
    :param font_type: 验证码使用字体
    :param length: 验证码字符个数
    :param draw_lines: 是否划干扰线
    :param n_line: 干扰线的条数范围，格式元组，默认为(1, 2)，只有draw_lines为True时有效
    :param draw_points: 是否画干扰点
    :param point_chance: 干扰点出现的概率，大小范围[0, 100]
    :return: PIL Image实例， 验证码图片中的字符串
    """

    width, height = size  # 宽和高
    img = Image.new(mode, size, bg_color)  # 创建图形
    draw = ImageDraw.Draw(img)  # 创建画笔

    def get_chars():
        """生成给定长度的字符串，返回列表格式"""
        return random.sample(chars, length)

    def create_lines():
        """绘制干扰线"""
        line_num = random.randint(*n_line)  # 干扰线条数
        for i in range(line_num):
            # 起始点
            begin = (random.randint(0, size[0]), random.randint(0, size[1]))
            # 结束点
            end = (random.randint(0, size[0]), random.randint(0, size[1]))
            draw.line([begin, end], fill=(0, 0, 0))

    def create_points():
        """绘制干扰点"""
        chance = min(100, max(0, int(point_chance)))  # 大小限制在[0, 100]
        for w in range(width):
            for h in range(height):
                tmp = random.randint(0, 100)
                if tmp > 100 - chance:
                    draw.point((w, h), fill=(0, 0, 0))

    def create_strs():
        """绘制验证码字符"""
        c_chars = get_chars()
        strs = ' %s ' % ' '.join(c_chars)  # 每个字符前后以空格隔开
        font = ImageFont.truetype(font_type, font_size)
        font_width, font_height = font.getsize(strs)
        draw.text(((width - font_width) / 3, (height - font_height) / 3), strs, font=font, fill=fg_color)
        return ''.join(c_chars)

    if draw_lines:
        create_lines()
    if draw_points:
        create_points()
    strs = create_strs()

    # 图形扭曲参数
    params = [
        1 - float(random.randint(1, 2)) / 100,
        0,
        0,
        0,
        1 - float(random.randint(1, 10)) / 100,
        float(random.randint(1, 2)) / 500,
        0.001,
        float(random.randint(1, 2)) / 500
    ]

    img = img.transform(size, Image.PERSPECTIVE, params)  # 创建扭曲
    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)  # 滤镜，边界加强（阈值更大）
    return img, strs


def admin_required(func):
    """检查是否需要admin权限的装饰器

    :param func: 需要装饰的函数
    :return: 装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        """通过'is_admin'函数判断用户角色"""
        if not current_user.is_admin():
            abort(403)
        return func(*args, **kwargs)
    return wrapper
