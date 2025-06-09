#!/usr/bin/env python3
"""
Synthetic Data Generator for OptimoV2
Generates test data for the school scheduling system
"""

import pandas as pd
import random
import numpy as np
import math
import yaml
import argparse
from pathlib import Path
import sys
import io

# Fix for Windows console encoding issues
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def generate_synthetic_data(output_path, students_per_grade=25):
    """Generate synthetic scheduling data for testing"""
    
    # Constants (keeping your exact ratios)
    STUDENTS_PER_GRADE = students_per_grade
    SECTION_SIZES = {
        'default': 25,  
        'lab': 30,      
        'PE': 35,       
        'special': 15   
    }
    MIN_SECTIONS_PER_COURSE = 2  # Ensure at least 2 sections per course

    SPED_RATIO = 0.15  # 15% SPED students to test distribution
    SPECIAL_COURSE_RATIO = 0.3  # Only 30% of students get special courses

    # Add new constants
    MAX_SCIENCE_SECTIONS = 3  # Maximum science sections per teacher
    SPECIAL_SECTIONS_PER_COURSE = 2  # Limit sections for Medical Career and Heroes Teach

    # Modify SPECIAL_COURSE_RATIO to ensure we don't exceed capacity
    max_special_students = SPECIAL_SECTIONS_PER_COURSE * SECTION_SIZES['special']
    SPECIAL_COURSE_RATIO = min(0.3, max_special_students / (STUDENTS_PER_GRADE * 4))

    # Course patterns by grade
    COURSE_PATTERNS = {
        9: [
            ['English 9', 'Math 1', 'Biology', 'World History', 'PE', 'Medical Career'],
            ['English 9', 'Math 1', 'Biology', 'World History', 'PE', 'Heroes Teach'],
            ['English 9', 'Math 1', 'Biology', 'World History', 'PE', 'Study Hall']  # Non-special alternative
        ],
        10: [
            ['English 10', 'Math 2', 'Chemistry', 'US History', 'PE', 'Medical Career'],
            ['English 10', 'Math 2', 'Chemistry', 'US History', 'PE', 'Heroes Teach'],
            ['English 10', 'Math 2', 'Chemistry', 'US History', 'PE', 'Study Hall']  # Non-special alternative
        ],
        11: [
            ['English 11', 'Math 3', 'Physics', 'Government', 'Sports Med', 'Medical Career'],
            ['English 11', 'Math 3', 'Physics', 'Government', 'Sports Med', 'Heroes Teach'],
            ['English 11', 'Math 3', 'Physics', 'Government', 'Sports Med', 'Study Hall']  # Non-special alternative
        ],
        12: [
            ['English 12', 'Math 4', 'AP Biology', 'Economics', 'Sports Med', 'Medical Career'],
            ['English 12', 'Math 4', 'AP Biology', 'Economics', 'Sports Med', 'Heroes Teach'],
            ['English 12', 'Math 4', 'AP Biology', 'Economics', 'Sports Med', 'Study Hall']  # Non-special alternative
        ]
    }

    # Calculate unique courses first
    unique_courses = set()
    for patterns in COURSE_PATTERNS.values():
        for pattern in patterns:
            unique_courses.update(pattern)

    # Generate student data
    students = []
    student_preferences = []
    student_id = 1
    
    for grade in COURSE_PATTERNS:
        for _ in range(STUDENTS_PER_GRADE):
            student_id_str = f"ST{student_id:03d}"
            is_sped = random.random() < SPED_RATIO
            
            # Determine if student gets a special course
            gets_special = random.random() < SPECIAL_COURSE_RATIO
            
            students.append({
                'Student ID': student_id_str,
                'SPED': "Yes" if is_sped else "No"
            })
            
            # Select course pattern based on special course availability
            if gets_special:
                pattern = random.choice(COURSE_PATTERNS[grade][:2])  # Only special patterns
            else:
                pattern = COURSE_PATTERNS[grade][2]  # Non-special pattern
                
            student_preferences.append({
                'Student ID': student_id_str,
                'Preferred Sections': ';'.join(pattern)
            })
            
            student_id += 1

    # Generate teacher data
    num_students = len(students)
    num_teachers = math.ceil(num_students / 20)  # 20:1 ratio
    
    # Update departments list to include Study Hall
    departments = {
        'English': ['English 9', 'English 10', 'English 11', 'English 12'],
        'Math': ['Math 1', 'Math 2', 'Math 3', 'Math 4'],
        'Science': ['Biology', 'Chemistry', 'Physics', 'AP Biology'],
        'Social Studies': ['World History', 'US History', 'Government', 'Economics'],
        'PE': ['PE', 'Sports Med'],
        'Special': ['Medical Career', 'Heroes Teach'],
        'General': ['Study Hall']  
    }

    # Helper functions
    def get_section_size(course):
        if 'Biology' in course or 'Chemistry' in course or 'Physics' in course:
            return SECTION_SIZES['lab']
        elif 'PE' in course:
            return SECTION_SIZES['PE']
        elif course in ['Medical Career', 'Heroes Teach', 'Sports Med']:
            return SECTION_SIZES['special']
        return SECTION_SIZES['default']

    def get_department(course):
        if course == 'Study Hall':
            return 'General'
        for dept, courses in departments.items():
            if any(course.startswith(c) for c in courses):
                return dept
        return 'General'

    # Calculate total sections needed per department first
    dept_sections = {dept: 0 for dept in departments}  # Now includes 'General'
    for course in unique_courses:
        total_requests = sum(1 for prefs in student_preferences 
                           if course in prefs['Preferred Sections'].split(';'))
        num_sections = max(2, math.ceil(total_requests / SECTION_SIZES['default']))
        
        # Find which department this course belongs to
        for dept, courses in departments.items():
            if any(c in course for c in courses):
                dept_sections[dept] += num_sections
                break

    # Calculate required teachers per department
    def calculate_required_teachers():
        dept_course_counts = {dept: 0 for dept in departments}
        for grade_patterns in COURSE_PATTERNS.values():
            for pattern in grade_patterns:
                for course in pattern:
                    dept = get_department(course)
                    dept_course_counts[dept] += STUDENTS_PER_GRADE / len(grade_patterns)

        required_teachers = {}
        for dept, count in dept_course_counts.items():
            if dept == 'Science':
                # Increase science teachers to accommodate MAX_SCIENCE_SECTIONS constraint
                total_science_sections = sum(
                    math.ceil(STUDENTS_PER_GRADE / SECTION_SIZES['lab'])
                    for grade in COURSE_PATTERNS.values()
                    for pattern in grade
                    for course in pattern
                    if course in ['Biology', 'Chemistry', 'Physics', 'AP Biology']
                )
                required_teachers[dept] = math.ceil(total_science_sections / MAX_SCIENCE_SECTIONS)
            elif dept == 'General':
                required_teachers[dept] = 2  # Minimum teachers for Study Hall
            else:
                section_size = SECTION_SIZES['special'] if dept == 'Special' else SECTION_SIZES['default']
                required_teachers[dept] = math.ceil(count / (section_size * 4))
            # Ensure minimum of 2 teachers per department
            required_teachers[dept] = max(2, required_teachers[dept])
        
        return required_teachers

    # Modify teacher generation for special courses
    def generate_teachers():
        teachers = []
        teacher_id = 1

        # Create dedicated special course teachers
        special_teachers = [
            {
                'Teacher ID': f"T{teacher_id:03d}",
                'Department': 'Special',
                'Dedicated Course': 'Medical Career',
                'Current Load': 0,
                'Science Sections': 0
            },
            {
                'Teacher ID': f"T{teacher_id+1:03d}",
                'Department': 'Special',
                'Dedicated Course': 'Heroes Teach',
                'Current Load': 0,
                'Science Sections': 0
            }
        ]
        teachers.extend(special_teachers)
        teacher_id += 2

        # Get required teachers per department
        required_teachers = calculate_required_teachers()

        for dept, num_required in required_teachers.items():
            if dept != 'Special':
                for _ in range(num_required):
                    teachers.append({
                        'Teacher ID': f"T{teacher_id:03d}",
                        'Department': dept,
                        'Dedicated Course': None,
                        'Current Load': 0,
                        'Science Sections': 0
                    })
                    teacher_id += 1

        return teachers, {t['Dedicated Course']: t['Teacher ID'] 
                        for t in special_teachers if t['Dedicated Course']}

    # Add this function definition before section creation
    def assign_teacher_to_section(course, dept, teachers, special_course_teachers):
        """Assign a teacher to a section based on department and availability"""
        MAX_COURSES_PER_TEACHER = 4  # Maximum number of courses per teacher

        # Handle special courses
        if course in special_course_teachers:
            teacher_id = special_course_teachers[course]
            teacher = next(t for t in teachers if t['Teacher ID'] == teacher_id)
            teacher['Current Load'] += 1
            return teacher_id

        dept_teachers = [t for t in teachers if t['Department'] == dept]
        is_science_course = course in ['Biology', 'Chemistry', 'Physics', 'AP Biology']

        if is_science_course:
            # Filter science teachers based on science section constraint
            available_teachers = [
                t for t in dept_teachers
                if t['Current Load'] < MAX_COURSES_PER_TEACHER
                and t['Science Sections'] < MAX_SCIENCE_SECTIONS
            ]
        else:
            available_teachers = [
                t for t in dept_teachers
                if t['Current Load'] < MAX_COURSES_PER_TEACHER
            ]

        available_teachers.sort(key=lambda t: (t['Current Load'], t['Science Sections']))

        if not available_teachers:
            new_teacher_id = f"T{len(teachers) + 1:03d}"
            new_teacher = {
                'Teacher ID': new_teacher_id,
                'Department': dept,
                'Dedicated Course': None,
                'Current Load': 1,
                'Science Sections': 1 if is_science_course else 0
            }
            teachers.append(new_teacher)
            return new_teacher_id

        chosen_teacher = available_teachers[0]
        chosen_teacher['Current Load'] += 1
        if is_science_course:
            chosen_teacher['Science Sections'] += 1
        return chosen_teacher['Teacher ID']

    # Get teachers and special course mappings
    teachers, special_course_teachers = generate_teachers()
    
    # Initialize teacher loads
    teacher_loads = {t['Teacher ID']: 0 for t in teachers}

    # Create sections with special course handling
    sections = []
    section_id = 1

    # Calculate course demands first
    course_demands = []
    for course in unique_courses:
        total_requests = sum(1 for prefs in student_preferences 
                           if course in prefs['Preferred Sections'].split(';'))
        course_demands.append((course, total_requests))
    
    # Sort by demand
    course_demands.sort(key=lambda x: x[1], reverse=True)

    # Handle special courses first
    special_courses = ['Medical Career', 'Heroes Teach']
    for course in special_courses:
        teacher_id = special_course_teachers[course]
        for _ in range(SPECIAL_SECTIONS_PER_COURSE):
            sections.append({
                'Section ID': f"S{section_id:03d}",
                'Course ID': course,
                'Teacher Assigned': teacher_id,
                '# of Seats Available': SECTION_SIZES['special'],
                'Department': 'Special'
            })
            section_id += 1
            teacher_loads[teacher_id] += 1

    # Modify section creation for better capacity distribution
    def create_course_sections(course, requests):
        """Create sections for a course with appropriate capacity"""
        section_size = get_section_size(course)
        
        # Calculate minimum sections needed for capacity
        min_sections_needed = math.ceil(requests / section_size)
        
        # Always create at least 2 sections, and ensure enough capacity
        num_sections = max(MIN_SECTIONS_PER_COURSE, min_sections_needed)
        
        # Add buffer capacity to ensure sections start around 75-85% utilization
        # This gives the optimizer room to work without starting at extremes
        target_initial_utilization = 0.80  # Target 80% initial utilization
        ideal_sections = math.ceil(requests / (section_size * target_initial_utilization))
        num_sections = max(num_sections, ideal_sections)
        
        # Don't create too many sections (avoid starting with very low utilization)
        max_sections = math.ceil(requests / (section_size * 0.60))  # Don't go below 60%
        num_sections = min(num_sections, max_sections)
            
        return num_sections, section_size

    # Then handle regular courses
    regular_courses = [c for c in course_demands if c[0] not in special_courses]
    for course, total_requests in regular_courses:
        num_sections, section_size = create_course_sections(course, total_requests)
        dept = get_department(course)
        
        for _ in range(num_sections):
            teacher_id = assign_teacher_to_section(course, dept, teachers, special_course_teachers)
            sections.append({
                'Section ID': f"S{section_id:03d}",
                'Course ID': course,
                'Teacher Assigned': teacher_id,
                '# of Seats Available': section_size,
                'Department': dept
            })
            section_id += 1

    # Generate teacher unavailability (to test constraints)
    periods = ['R1', 'R2', 'R3', 'R4', 'G1', 'G2', 'G3', 'G4']
    unavailability = []
    
    for teacher in teachers:
        if random.random() < 0.05:  # Reduced chance of unavailability to 5%
            unavail_periods = random.sample(periods, 1)  # Only 1 period unavailable
            unavailability.append({
                'Teacher ID': teacher['Teacher ID'],
                'Unavailable Periods': ','.join(unavail_periods)
            })

    # Generate Period.csv file
    period_data = []
    for i, period in enumerate(periods):
        period_data.append({
            'period_id': i + 1,
            'period_name': period
        })

    # Save all files
    pd.DataFrame(students).to_csv(f"{output_path}/Student_Info.csv", index=False)
    pd.DataFrame(student_preferences).to_csv(f"{output_path}/Student_Preference_Info.csv", index=False)
    pd.DataFrame(teachers).to_csv(f"{output_path}/Teacher_Info.csv", index=False)
    pd.DataFrame(sections).to_csv(f"{output_path}/Sections_Information.csv", index=False)
    pd.DataFrame(unavailability).to_csv(f"{output_path}/Teacher_unavailability.csv", index=False)
    pd.DataFrame(period_data).to_csv(f"{output_path}/Period.csv", index=False)
    
    # Print summary
    print("\nGenerated synthetic data:")
    print(f"  Students: {len(students)} ({STUDENTS_PER_GRADE} per grade)")
    print(f"  Teachers: {len(teachers)}")
    print(f"  Sections: {len(sections)}")
    print(f"  Courses: {len(unique_courses)}")
    print(f"  SPED Students: {sum(1 for s in students if s['SPED'] == 'Yes')}")
    print(f"  Special Course Students: ~{int(len(students) * SPECIAL_COURSE_RATIO)}")
    # Fix Unicode issue by encoding the path
    try:
        print(f"\nFiles saved to: {output_path}")
    except UnicodeEncodeError:
        # Fallback to ASCII representation
        safe_path = output_path.encode('ascii', 'replace').decode('ascii')
        print(f"\nFiles saved to: {safe_path}")


def main():
    """Main entry point with command line arguments"""
    
    parser = argparse.ArgumentParser(description='Generate synthetic test data for OptimoV2')
    parser.add_argument('--size', type=str, choices=['small', 'medium', 'large'], 
                       default='small', help='School size preset')
    parser.add_argument('--students-per-grade', type=int, 
                       help='Override students per grade (ignores --size)')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Set random seed if provided
    if args.seed:
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    # Determine students per grade
    if args.students_per_grade:
        students_per_grade = args.students_per_grade
    else:
        # Load from config
        config_path = Path(__file__).parent.parent / 'config' / 'settings.yaml'
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                sizes = config.get('synthetic_data', {}).get('sizes', {})
                students_per_grade = sizes.get(args.size, 25)
        else:
            # Default sizes if no config
            size_map = {'small': 25, 'medium': 125, 'large': 500}
            students_per_grade = size_map[args.size]
    
    # Set output path
    output_path = Path(__file__).parent.parent / 'data' / 'base'
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {args.size} school data ({students_per_grade} students per grade)...")
    
    # Generate the data
    generate_synthetic_data(str(output_path), students_per_grade)


if __name__ == "__main__":
    main()