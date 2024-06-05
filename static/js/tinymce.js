tinymce.init({
    selector: 'textarea#id_body',
    height: 500,
    menubar: false,
    plugins: [
        'advlist autolink lists link image charmap print preview anchor',
        'searchreplace visualblocks code fullscreen',
        'insertdatetime media table paste code help wordcount'
    ],
    toolbar: 'undo redo | formatselect | bold italic backcolor | \
              alignleft aligncenter alignright alignjustify | styleselect | bold italic | link image | \
              bullist numlist outdent indent | removeformat | help',
    content_style: 'p { margin-bottom: 0.05em; }',
});
