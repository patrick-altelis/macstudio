import re

def update_companies_file():
    with open('backend/routes/companies.py', 'r') as file:
        content = file.read()
    
    # Trouver et remplacer la fonction sync_pennylane_customers
    new_sync_function = '''@bp.route("/sync/pennylane", methods=["POST"])
def sync_pennylane_customers():
    """Sync customers from Pennylane."""
    try:
        logging.info("Starting Pennylane sync process...")

        # Get Pennylane API instance
        pennylane_api: PennylaneAPI = current_app.config['PENNYLANE_API']
        if not pennylane_api:
            raise Exception("PennylaneAPI not initialized")

        # Fetch customers from Pennylane
        logging.info("Fetching customers from Pennylane...")
        customers = pennylane_api.get_customers()
        logging.info(f"Retrieved {len(customers)} customers from Pennylane")

        # Insert or update customers in database
        with db.engine.connect() as conn:
            affected_rows = 0
            for customer in customers:
                # Transformer les données pour correspondre à la structure de la table
                customer_data = {
                    'pennylane_id': customer.get('id'),  # Changer 'id' en 'pennylane_id'
                    'name': customer.get('name'),
                    'email': customer.get('email'),
                    'address': str(customer.get('address')) if customer.get('address') else None
                }
                
                result = conn.execute(
                    text("""
                        INSERT INTO pennylane_customers (
                            pennylane_id, name, email, address, created_at, updated_at
                        ) VALUES (
                            :pennylane_id, :name, :email, :address, NOW(), NOW()
                        )
                        ON CONFLICT (pennylane_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            email = EXCLUDED.email,
                            address = EXCLUDED.address,
                            updated_at = NOW()
                        RETURNING id
                    """),
                    customer_data
                )
                affected_rows += result.rowcount
            conn.commit()

        return jsonify({
            'status': 'success',
            'total_processed': affected_rows,
            'total_errors': 0,
            'message': f'Successfully synced {affected_rows} customers'
        }), 200

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error during Pennylane sync: {error_msg}", exc_info=True)
        return jsonify({
            'status': 'error',
            'total_processed': 0,
            'total_errors': 1,
            'message': f'Sync failed: {error_msg}'
        }), 500'''
    
    content = re.sub(
        r'@bp\.route\("/sync/pennylane", methods=\["POST"\]\).*?}), 500',
        new_sync_function,
        content,
        flags=re.DOTALL
    )
    
    with open('backend/routes/companies.py', 'w') as file:
        file.write(content)

if __name__ == "__main__":
    update_companies_file()
    print("companies.py mis à jour avec succès!")
