//显示模态窗口
function showModal() {
    $('#confirm-modal-post')
        .on('show.bs.modal',function(e) {
            $(e.currentTarget).find('.btn-ok').data('href', $(e.relatedTarget).data('href'));
            $(e.currentTarget).find('.btn-ok').data('id', $(e.relatedTarget).data('id'));
            $(e.currentTarget).find('.btn-ok').data('bid', $(e.relatedTarget).data('bid'));
            $(e.currentTarget).find('.btn-ok').data('action', $(e.relatedTarget).data('action'));
        })

      .on('click', '.btn-ok', function (e) {
          var href = $(this).data('href');
          var id = $(this).data('id');
          var bid = $(this).data('bid');
          var action = $(this).data('action');

          submit(href, 'POST', [
              {name: 'id', value: id},
              {name: 'bid', value: bid},
              {name: 'action', value: action}
          ]);
      })

      .on('hidden.bs.modal', function(){
          location.reload(false)

      });
}

//获取删除对象对应名称（基于modalId，将'data-name'值赋予‘modal-body-name’元素）
function getModalBodyName() {
    $(".modalId").click(function(){
        document.getElementById('modal-body-name').innerHTML = $(this).data("name");
    });
}

//隐藏表单提交
function submit(action, method, values) {
    var form = $('<form/>', {
        action: action,
        method: method
    });
    $.each(values, function () {
        form.append($('<input/>', {
            type: 'hidden',
            name: this.name,
            value: this.value
        }));
    });
    form.appendTo('body').submit();
}
