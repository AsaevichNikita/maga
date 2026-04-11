(function () {
  window.promptCourseStudents = function () {
    const courseId = window.promptId('Введите ID курса:');
    if (courseId) window.makeRequest('GET', `/courses/${courseId}/students`);
  };

  window.promptCourseSlots = function () {
    const courseId = window.promptId('Введите ID курса:');
    if (courseId) window.makeRequest('GET', `/courses/${courseId}/slots`);
  };
})();