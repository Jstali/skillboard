"""
Create sample skills and templates for Skillboard testing
"""
import psycopg2
from datetime import datetime

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/skillboard"

def create_sample_data():
    print("Creating sample skills and templates...")
    
    # Sample skills organized by category
    skills = [
        # Programming Languages
        ("Python", "Programming", "Python programming language"),
        ("JavaScript", "Programming", "JavaScript programming language"),
        ("Java", "Programming", "Java programming language"),
        ("TypeScript", "Programming", "TypeScript programming language"),
        ("Go", "Programming", "Go programming language"),
        
        # Cloud & Infrastructure
        ("AWS", "Cloud", "Amazon Web Services"),
        ("Azure", "Cloud", "Microsoft Azure"),
        ("GCP", "Cloud", "Google Cloud Platform"),
        ("Kubernetes", "Cloud", "Container orchestration"),
        
        # DevOps & Tools
        ("Docker", "DevOps", "Container technology"),
        ("CI/CD", "DevOps", "Continuous Integration/Deployment"),
        ("Git", "DevOps", "Version control"),
        ("Jenkins", "DevOps", "Automation server"),
        
        # Frontend
        ("React", "Frontend", "React framework"),
        ("Vue.js", "Frontend", "Vue.js framework"),
        ("HTML/CSS", "Frontend", "Web fundamentals"),
        ("Angular", "Frontend", "Angular framework"),
        
        # Backend
        ("Node.js", "Backend", "Node.js runtime"),
        ("FastAPI", "Backend", "FastAPI framework"),
        ("Django", "Backend", "Django framework"),
        ("Spring Boot", "Backend", "Spring Boot framework"),
        
        # Database
        ("PostgreSQL", "Database", "PostgreSQL database"),
        ("MongoDB", "Database", "MongoDB database"),
        ("Redis", "Database", "Redis cache"),
        ("SQL", "Database", "SQL query language"),
        
        # Soft Skills
        ("Communication", "Soft Skills", "Effective communication"),
        ("Leadership", "Soft Skills", "Team leadership"),
        ("Problem Solving", "Soft Skills", "Analytical thinking"),
        ("Agile", "Soft Skills", "Agile methodology"),
    ]
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Create skills
        print("\n1. Creating skills...")
        skill_ids = {}
        for name, category, description in skills:
            try:
                cur.execute("""
                    INSERT INTO skills (name, category, description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        category = EXCLUDED.category,
                        description = EXCLUDED.description
                    RETURNING id
                """, (name, category, description))
                skill_id = cur.fetchone()[0]
                skill_ids[name] = skill_id
                print(f"   ✅ {name} ({category})")
            except Exception as e:
                # If conflict, get existing ID
                cur.execute("SELECT id FROM skills WHERE name = %s", (name,))
                result = cur.fetchone()
                if result:
                    skill_ids[name] = result[0]
                print(f"   ℹ️  {name} (already exists)")
        
        # Create templates for different bands
        print("\n2. Creating skill templates...")
        
        # Template 1: Junior Developer (Band A)
        templates = [
            {
                "name": "Junior Developer - Band A",
                "category": "Technical",
                "description": "Skills required for junior developers",
                "skills": [
                    ("Python", "intermediate"),
                    ("JavaScript", "beginner"),
                    ("Git", "beginner"),
                    ("HTML/CSS", "intermediate"),
                    ("SQL", "beginner"),
                    ("Communication", "intermediate"),
                    ("Problem Solving", "beginner"),
                ]
            },
            {
                "name": "Mid-Level Developer - Band B",
                "category": "Technical",
                "description": "Skills required for mid-level developers",
                "skills": [
                    ("Python", "advanced"),
                    ("JavaScript", "intermediate"),
                    ("TypeScript", "intermediate"),
                    ("React", "intermediate"),
                    ("Node.js", "intermediate"),
                    ("Docker", "intermediate"),
                    ("AWS", "intermediate"),
                    ("PostgreSQL", "intermediate"),
                    ("Git", "advanced"),
                    ("CI/CD", "intermediate"),
                    ("Communication", "advanced"),
                    ("Problem Solving", "intermediate"),
                    ("Agile", "intermediate"),
                ]
            },
            {
                "name": "Senior Developer - Band L1",
                "category": "Technical",
                "description": "Skills required for senior developers",
                "skills": [
                    ("Python", "expert"),
                    ("JavaScript", "advanced"),
                    ("TypeScript", "advanced"),
                    ("React", "advanced"),
                    ("Node.js", "advanced"),
                    ("Docker", "advanced"),
                    ("Kubernetes", "intermediate"),
                    ("AWS", "advanced"),
                    ("PostgreSQL", "advanced"),
                    ("MongoDB", "intermediate"),
                    ("Git", "expert"),
                    ("CI/CD", "advanced"),
                    ("Communication", "expert"),
                    ("Leadership", "advanced"),
                    ("Problem Solving", "advanced"),
                    ("Agile", "advanced"),
                ]
            },
            {
                "name": "Data Scientist - Band B",
                "category": "Technical",
                "description": "Skills required for data scientists",
                "skills": [
                    ("Python", "expert"),
                    ("SQL", "advanced"),
                    ("PostgreSQL", "intermediate"),
                    ("MongoDB", "beginner"),
                    ("AWS", "intermediate"),
                    ("Git", "intermediate"),
                    ("Communication", "advanced"),
                    ("Problem Solving", "advanced"),
                ]
            },
            {
                "name": "Consultant - Band A",
                "category": "Consulting",
                "description": "Skills required for consultants",
                "skills": [
                    ("Communication", "advanced"),
                    ("Problem Solving", "advanced"),
                    ("Leadership", "intermediate"),
                    ("Agile", "intermediate"),
                    ("Python", "beginner"),
                    ("SQL", "beginner"),
                ]
            }
        ]
        
        for template in templates:
            try:
                # Create template
                cur.execute("""
                    INSERT INTO team_skill_templates (name, category, description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        category = EXCLUDED.category,
                        description = EXCLUDED.description
                    RETURNING id
                """, (template["name"], template["category"], template["description"]))
                template_id = cur.fetchone()[0]
                print(f"   ✅ {template['name']}")
                
                # Add skills to template
                for skill_name, level in template["skills"]:
                    if skill_name in skill_ids:
                        try:
                            cur.execute("""
                                INSERT INTO template_skills (template_id, skill_id, required_level)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (template_id, skill_id) DO UPDATE SET
                                    required_level = EXCLUDED.required_level
                            """, (template_id, skill_ids[skill_name], level))
                        except Exception as e:
                            print(f"      ⚠️  Error adding {skill_name}: {e}")
                
            except Exception as e:
                print(f"   ⚠️  {template['name']}: {e}")
        
        # Count totals
        cur.execute("SELECT COUNT(*) FROM skills")
        total_skills = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM team_skill_templates")
        total_templates = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"\n✅ Sample data created successfully!")
        print(f"\n📊 Summary:")
        print(f"   - Total skills: {total_skills}")
        print(f"   - Total templates: {total_templates}")
        print("\n" + "="*60)
        print("TEMPLATES CREATED:")
        print("="*60)
        print("1. Junior Developer - Band A (7 skills)")
        print("2. Mid-Level Developer - Band B (13 skills)")
        print("3. Senior Developer - Band L1 (16 skills)")
        print("4. Data Scientist - Band B (8 skills)")
        print("5. Consultant - Band A (6 skills)")
        print("="*60)
        print("\n✅ You can now assign these templates to employees!")
        print("   Go to: Admin Dashboard → Template Assignment")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_sample_data()
