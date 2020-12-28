class CourseParticipant:
    def __init__(self, name, surname):
        self.name = name
        self.surname = surname

    def __str__(self):
        return f'Имя: {self.name}\nФамилия: {self.surname}\n'


class Student(CourseParticipant):
    def __init__(self, name, surname, gender):
        super().__init__(name, surname)
        self.gender = gender
        self.finished_courses = []
        self.courses_in_progress = []
        self.grades = {}

    def rate_lecturer(self, lecturer, course, score):
        if isinstance(lecturer, Lecturer) and (course in self.finished_courses or course in self.courses_in_progress) and score <= 10:
            if course in lecturer.courses_attached and lecturer.scores.get(course) is not None:
                lecturer.scores[course] += [score]
            elif course in lecturer.courses_attached and lecturer.scores.get(course) is None:
                lecturer.scores[course] = [score]
        else:
            return 'Ошибка'

    def __str__(self):
        avgGrade = self.__get_avg_grade()
        return super().__str__() + f'Средняя оценка за домашние задания: {avgGrade}\n' \
                                   f'Курсы в процессе изучения: {", ".join(self.courses_in_progress)}\n' \
                                   f'Завершенные курсы: {", ".join(self.finished_courses)}'

    def __le__(self, other):
        if isinstance(other, Student):
            return self.__get_avg_grade() <= other.__get_avg_grade()

    def __lt__(self, other):
        if isinstance(other, Student):
            return self.__get_avg_grade() < other.__get_avg_grade()

    def __eq__(self, other):
        if isinstance(other, Student):
            return self.__get_avg_grade() == other.__get_avg_grade()

    def __get_avg_grade(self):
        flat_grades_list = []
        for course_grades in self.grades.values():
            for grade in course_grades:
                flat_grades_list.append(grade)
        return (max(flat_grades_list) + min(flat_grades_list)) / 2


class Mentor(CourseParticipant):
    def __init__(self, name, surname):
        super().__init__(name, surname)
        self.courses_attached = []


class Lecturer(Mentor):
    def __init__(self, name, surname):
        super().__init__(name, surname)
        self.scores = {}

    def __str__(self):
        avgScore = self.__get_avg_score()
        return super(Lecturer, self).__str__() + f'Средняя оценка за лекции: {avgScore}\n'

    def __get_avg_score(self):
        flat_scores_list = []
        for course_scores in self.scores.values():
            for score in course_scores:
                flat_scores_list.append(score)
        return (max(flat_scores_list) + min(flat_scores_list)) / 2

    def __le__(self, other):
        if isinstance(other, Lecturer):
            return self.__get_avg_score() <= other.__get_avg_score()

    def __lt__(self, other):
        if isinstance(other, Lecturer):
            return self.__get_avg_score() < other.__get_avg_score()

    def __eq__(self, other):
        if isinstance(other, Lecturer):
            return self.__get_avg_score() == other.__get_avg_score()


class Reviewer (Mentor):
    def __init__(self, name, surname):
        super().__init__(name, surname)

    def rate_hw(self, student, course, grade):
        if isinstance(student, Student) and course in self.courses_attached and course in student.courses_in_progress:
            if course in student.grades:
                student.grades[course] += [grade]
            else:
                student.grades[course] = [grade]
        else:
            return 'Ошибка'


class CourseParticipantStatisticCounter:
    def __init__(self, iterator_items, filter_value):
        self.iterator = iterator_items
        self.filter = filter_value

    def get_statistic_result(self):
        result_scores = []
        for item in self.iterator:
            if isinstance(item, Student) and self.filter in item.grades.keys():
                result_scores += item.grades[self.filter]
            elif isinstance(item, Lecturer) and self.filter in item.scores.keys():
                result_scores += item.scores[self.filter]
        if len(result_scores) > 0:
            return (max(result_scores) + min(result_scores)) / 2
        else:
            return 'Нет данных'


if __name__ == '__main__':
    student_1 = Student('Ruoy', 'Eman', 'm')
    student_1.courses_in_progress += ['Python', 'C++']

    student_2 = Student('Sergant', 'Pain', 'm')
    student_2.courses_in_progress += ['C++']

    reviewer_1 = Reviewer('Entony', 'Cloudfinger')
    reviewer_1.courses_attached += ['C++']
    reviewer_2 = Reviewer('Sunny', 'ElseIffer')
    reviewer_2.courses_attached += ['Python']

    reviewer_1.rate_hw(student_1, 'C++', 5)
    reviewer_1.rate_hw(student_2, 'C++', 5)

    reviewer_2.rate_hw(student_1, 'Python', 5)
    reviewer_2.rate_hw(student_2, 'Python', 5)

    lector_1 = Lecturer('Smarty', 'Newthinker')
    lector_2 = Lecturer('Arry', 'Trycatcher')
    lector_1.courses_attached += ['Python', 'C++']
    lector_2.courses_attached += ['C++']

    student_1.rate_lecturer(lector_1, 'Python', 5)
    student_1.rate_lecturer(lector_2, 'C++', 8)

    student_2.rate_lecturer(lector_1, 'C++', 3)
    student_2.rate_lecturer(lector_2, 'C++', 9)

    students_list = [student_1, student_2]
    lectors_list = [lector_1, lector_2]

    student_statistic = CourseParticipantStatisticCounter(students_list, 'Python')
    lectors_statistic = CourseParticipantStatisticCounter(lectors_list, 'C++')

    print(student_statistic.get_statistic_result())
    print(lectors_statistic.get_statistic_result())