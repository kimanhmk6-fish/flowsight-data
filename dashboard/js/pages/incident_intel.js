/* Incident Intelligence — wrapper với 4 sub-tabs */
(function () {
  FS.pages.incident_intel = {
    title: 'Quản lý & Phân tích Sự cố',
    sub: 'Vòng đời sự cố: giám sát → tác động → nguyên nhân → lan truyền',
    render(root) {
      FS.subtabs(root, [
        { key: 'incidents', label: 'Giám sát', page: 'incidents' },
        { key: 'impact', label: 'Phân tích tác động', page: 'impact' },
        { key: 'rootcause', label: 'Nguyên nhân gốc', page: 'rootcause' },
        { key: 'propagation', label: 'Đồ thị lan truyền', page: 'propagation' },
      ], 'incidents');
    }
  };
})();
