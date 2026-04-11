(function () {
  window.getMyTeacherOfferingSlots = function () {
    const academicYear = prompt('Укажи учебный год, например 2026/2027:', '2026/2027');
    if (!academicYear) return;
    window.makeRequest('GET', `/teacher-offering-slots/my?academic_year=${encodeURIComponent(academicYear)}`);
  };
})();