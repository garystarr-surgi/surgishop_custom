"""
API Endpoints for surgishop_custom
"""
import frappe


@frappe.whitelist(allow_guest=False)
def check_recall_inventory(recalls):
    """
    FDA Recall API
    Cross-reference FDA recalls against ERPNext inventory
    
    Args:
        recalls: List of recall dicts (already parsed by Frappe)
    
    Returns:
        dict with matched_count and matches list
    """
    # recalls should already be a list/dict, no parsing needed
    if not recalls:
        return {'success': False, 'matched_count': 0, 'matches': []}
    
    matches = []
    
    for recall in recalls:
        recall_number = recall.get('recall_number')
        product_code = recall.get('product_code')
        code_info = recall.get('code_info', '')
        device_name = recall.get('device_name')
        
        # Extract UDI from code_info
        udi_numbers = extract_udi_from_code_info(code_info)
        
        # Check 1: Match Product Code against Item Names
        if product_code:
            item_matches = frappe.get_all(
                'Item',
                filters={'item_name': product_code},
                fields=['name', 'item_name']
            )
            
            for item in item_matches:
                # Check if already exists
                if not frappe.db.exists('Recall Match', {
                    'recall_number': recall_number,
                    'erpnext_item_code': item.name,
                    'match_type': 'Item Name Match'
                }):
                    match = create_recall_match(
                        recall=recall,
                        match_type='Item Name Match',
                        item_code=item.name,
                        item_name=item.item_name
                    )
                    matches.append(match)
        
        # Check 2: Match UDI against Batch Numbers
        if udi_numbers:
            for udi in udi_numbers:
                batch_matches = frappe.db.sql("""
                    SELECT name, item, batch_id
                    FROM `tabBatch`
                    WHERE batch_id LIKE %s
                """, (f'%{udi}%',), as_dict=True)
                
                for batch in batch_matches:
                    # Get item name
                    item_name = frappe.db.get_value('Item', batch.item, 'item_name')
                    
                    # Check if already exists
                    if not frappe.db.exists('Recall Match', {
                        'recall_number': recall_number,
                        'erpnext_batch_number': batch.name,
                        'match_type': 'Batch UDI Match'
                    }):
                        match = create_recall_match(
                            recall=recall,
                            match_type='Batch UDI Match',
                            item_code=batch.item,
                            item_name=item_name,
                            batch_number=batch.name
                        )
                        matches.append(match)
    
    # Send email notification if matches found
    if matches:
        send_recall_notification(matches)
    
    frappe.db.commit()
    
    return {
        'success': True,
        'matched_count': len(matches),
        'matches': matches
    }


def extract_udi_from_code_info(code_info):
    """Extract UDI numbers from code_info text using simple string operations"""
    if not code_info:
        return []
    
    udi_numbers = []
    text = str(code_info).upper()
    
    # Split by newlines and process each line
    for line in text.split('\n'):
        if 'UDI' in line or 'GTIN' in line:
            # Remove common separators and split
            clean_line = line.replace(':', ' ').replace('(', ' ').replace(')', ' ').replace(',', ' ')
            words = clean_line.split()
            
            # Look for numeric strings that are 10+ digits (likely UDI/GTIN)
            for word in words:
                # Remove non-digit characters
                digits = ''.join(c for c in word if c.isdigit())
                if len(digits) >= 10:
                    udi_numbers.append(digits)
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for udi in udi_numbers:
        if udi not in seen:
            seen.add(udi)
            unique.append(udi)
    
    return unique


def create_recall_match(recall, match_type, item_code, item_name, batch_number=None):
    """Create a Recall Match record"""
    doc = frappe.get_doc({
        'doctype': 'Recall Match',
        'recall_number': recall.get('recall_number'),
        'fda_device_name': (recall.get('device_name', '') or '')[:140],
        'fda_product_code': (recall.get('product_code', '') or '')[:140],
        'match_type': match_type,
        'erpnext_item_code': item_code,
        'erpnext_item_name': item_name,
        'erpnext_batch_number': batch_number,
        'recall_date': recall.get('recall_date'),
        'recall_status': (recall.get('status', '') or '')[:140],
        'fda_reason': (recall.get('reason', '') or '')[:140],
        'notified': 0,
        'fda_recall_link': f'http://192.168.1.176/recall/{recall.get("id", "")}'
    })
    
    doc.insert(ignore_permissions=True)
    
    return {
        'name': doc.name,
        'recall_number': doc.recall_number,
        'item_code': doc.erpnext_item_code,
        'item_name': doc.erpnext_item_name,
        'batch_number': doc.erpnext_batch_number,
        'match_type': doc.match_type
    }


def send_recall_notification(matches):
    """Send email notification for recall matches"""
    
    # Build email content
    message = f"""
    <h2>FDA Recall Alert - Inventory Matches Found</h2>
    <p>{len(matches)} item(s) in your inventory match FDA recalls:</p>
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Recall Number</th>
            <th>Match Type</th>
            <th>Item Code</th>
            <th>Item Name</th>
            <th>Batch Number</th>
        </tr>
    """
    
    for match in matches:
        message += f"""
        <tr>
            <td>{match.get('recall_number', '')}</td>
            <td>{match.get('match_type', '')}</td>
            <td>{match.get('item_code', '')}</td>
            <td>{match.get('item_name', '')}</td>
            <td>{match.get('batch_number', 'N/A')}</td>
        </tr>
        """
    
    message += """
    </table>
    <p>Please review these items immediately in the FDA Recall Checker.</p>
    """
    
    # Send email
    frappe.sendmail(
        recipients=['gary.starr@surgishop.com'],
        subject=f'FDA Recall Alert - {len(matches)} Inventory Matches',
        message=message
    )
    
    # Mark as notified
    for match in matches:
        frappe.db.set_value('Recall Match', match['name'], 'notified', 1)
