"""
Create sample templates using correct table structure
"""
import psycopg2

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/skillboard"

def create_templates_fixed():
    print("Creating skill templates (fixed version)...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Get skill IDs
        cur.execute("SELECT id, name FROM skills")
        skills = {name: id for id, name in cur.fetchall()}
        
        # Templates using category_skill_templates
        # This table links skills to employee categories
        templates = {
            "Technical": [
                ("Python", "advanced", True, 1),
                ("JavaScript", "intermediate", True, 2),
                ("TypeScript", "intermediate", False, 3),
                ("React", "intermediate", False, 4),
                ("Node.js", "intermediate", False, 5),
                ("Docker", "intermediate", True, 6),
                ("AWS", "intermediate", False, 7),
                ("PostgreSQL", "intermediate", True, 8),
                ("Git", "advanced", True, 9),
                ("CI/CD", "intermediate", False, 10),
                ("Communication", "advanced", True, 11),
                ("Problem Solving", "intermediate", True, 12),
            ],
            "Consulting": [
                ("Communication", "expert", True, 1),
                ("Problem Solving", "advanced", True, 2),
                ("Leadership", "intermediate", True, 3),
                ("Agile", "intermediate", True, 4),
                ("Python", "beginner", False, 5),
                ("SQL", "beginner", False, 6),
            ]
        }
        
        print("\nCreating category-based skill templates...")
        for category, skill_list in templates.items():
            print(f"\n{category} Category:")
            for skill_name, level, is_required, order in skill_list:
                if skill_name in skills:
                    try:
                        cur.execute("""
                            INSERT INTO category_skill_templates 
                            (category, skill_id, required_level, is_required, display_order)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (category, skill_id) DO UPDATE SET
                                required_level = EXCLUDED.required_level,
                                is_required = EXCLUDED.is_required,
                                display_order = EXCLUDED.display_order
                        """, (category, skills[skill_name], level, is_required, order))
                        print(f"   ✅ {skill_name} ({level}) - Required: {is_required}")
                    except Exception as e:
                        print(f"   ⚠️  {skill_name}: {e}")
        
        # Count templates
        cur.execute("SELECT COUNT(DISTINCT category) FROM category_skill_templates")
        total_categories = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM category_skill_templates")
        total_skills = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"\n✅ Templates created successfully!")
        print(f"\n📊 Summary:")
        print(f"   - Categories with templates: {total_categories}")
        print(f"   - Total skill-category mappings: {total_skills}")
        print("\n" + "="*60)
        print("HOW TO USE:")
        print("="*60)
        print("1. Employees with category='Technical' will see Technical skills")
        print("2. Employees with category='Consulting' will see Consulting skills")
        print("3. Assign templates via Admin Dashboard → Template Assignment")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_templates_fixed()
