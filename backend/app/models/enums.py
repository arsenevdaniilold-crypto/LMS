import enum


class ClassType(str, enum.Enum):
    open = "open"
    closed = "closed"


class MemberRole(str, enum.Enum):
    teacher_creator = "teacher_creator"
    teacher = "teacher"
    student = "student"


class AssignmentType(str, enum.Enum):
    individual = "individual"
    group = "group"


class GradeType(str, enum.Enum):
    grade_0_5 = "0-5"
    grade_0_100 = "0-100"
    grade_0_1 = "0-1"


class GradingType(str, enum.Enum):
    uniform = "uniform"
    individual = "individual"


class MaterialType(str, enum.Enum):
    link = "link"
    file = "file"


class SolutionStatus(str, enum.Enum):
    created = "created"
    submitted = "submitted"
    returned = "returned"
    graded = "graded"
    pending_redistribution = "pending_redistribution"