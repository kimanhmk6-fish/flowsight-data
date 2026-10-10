/* Supply Chain & Traceability — wrapper với 2 sub-tabs */
(function () {
  FS.pages.supply_chain = {
    title: 'Vật tư & Truy xuất',
    sub: 'Dòng chảy vật tư và minh bạch nguồn gốc lô hàng',
    render(root) {
      FS.subtabs(root, [
        { key: 'genealogy', label: 'Truy vết Lot', page: 'genealogy' },
        { key: 'materials', label: 'Danh mục & Vật tư', page: 'materials' },
      ], 'genealogy');
    }
  };
})();
