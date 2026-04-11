(function () {
  window.getTeacherOfferingSlotsPublic = function () {
    window.makeRequest('GET', '/teacher-offering-slots/');
  };

  window.promptGetTeacherOfferingSlotPublic = function () {
    const slotId = window.promptId('Введите ID окна преподавателя:');
    if (slotId) {
      window.makeRequest('GET', `/teacher-offering-slots/${slotId}`);
    }
  };
})();