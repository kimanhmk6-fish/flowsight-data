/* System & Data Admin — wrapper với 5 sub-tabs (giới hạn Admin) */
(function () {
  FS.pages.admin = {
    title: 'Quản trị & Dữ liệu',
    sub: 'Hạ tầng dữ liệu và cấu hình hệ thống',
    render(root) {
      FS.subtabs(root, [
        { key: 'health', label: 'Chất lượng dữ liệu', page: 'health' },
        { key: 'import', label: 'Nhập & Ánh xạ', page: 'import' },
        { key: 'validation', label: 'Thẩm định', page: 'validation' },
        { key: 'architecture', label: 'Kiến trúc', page: 'architecture' },
        { key: 'guide', label: 'Hướng dẫn', page: 'guide' },
      ], 'health');
    }
  };
})();
