# core/ticket.py
import time
import random
import string
from core.db_instance import tickets  # فقط همین یک ایمپورت

def generate_ticket_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_ticket(user_id, question, chat_id, message_id):
    ticket_id = generate_ticket_id()
    ticket_data = {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'question': question,
        'chat_id': chat_id,
        'message_id': message_id,
        'status': 'open',
        'helper_id': None,
        'helper_group_message_id': None,
        'helper_message_id': None,
        'rating': None,
        'created_at': time.time(),
        'answered_at': None,
        'closed_at': None,
    }
    tickets.set_key(f"ticket_{ticket_id}", ticket_data)
    return ticket_id

def get_ticket(ticket_id):
    return tickets.get_key(f"ticket_{ticket_id}")

def update_ticket(ticket_id, **kwargs):
    ticket = get_ticket(ticket_id)
    if ticket:
        ticket.update(kwargs)
        tickets.set_key(f"ticket_{ticket_id}", ticket)
        return True
    return False

def get_user_tickets(user_id, status=None):
    all_keys = tickets.get_all_keys()
    result = []
    for key in all_keys:
        if key.startswith("ticket_"):
            ticket = tickets.get_key(key, {})
            if ticket.get('user_id') == user_id:
                if status is None or ticket.get('status') == status:
                    result.append(ticket)
    return result

def get_all_tickets(status=None):
    all_keys = tickets.get_all_keys()
    result = []
    for key in all_keys:
        if key.startswith("ticket_"):
            ticket = tickets.get_key(key, {})
            if status is None or ticket.get('status') == status:
                result.append(ticket)
    return result

def get_helper_stats(helper_id):
    all_keys = tickets.get_all_keys()
    total_answered = 0
    total_rating = 0
    count_rated = 0
    for key in all_keys:
        if key.startswith("ticket_"):
            ticket = tickets.get_key(key, {})
            if ticket.get('helper_id') == helper_id and ticket.get('status') in ['answered', 'closed']:
                total_answered += 1
                if ticket.get('rating'):
                    total_rating += ticket['rating']
                    count_rated += 1
    avg_rating = total_rating / count_rated if count_rated > 0 else 0
    return {'total_answered': total_answered, 'avg_rating': avg_rating, 'count_rated': count_rated}

def get_helper_leaderboard():
    all_keys = tickets.get_all_keys()
    helpers = {}
    for key in all_keys:
        if key.startswith("ticket_"):
            ticket = tickets.get_key(key, {})
            helper_id = ticket.get('helper_id')
            if helper_id and ticket.get('status') in ['answered', 'closed']:
                if helper_id not in helpers:
                    helpers[helper_id] = {'answered': 0, 'ratings': [], 'rated_count': 0}
                helpers[helper_id]['answered'] += 1
                if ticket.get('rating'):
                    helpers[helper_id]['ratings'].append(ticket['rating'])
                    helpers[helper_id]['rated_count'] += 1
    result = []
    for hid, data in helpers.items():
        avg = sum(data['ratings']) / len(data['ratings']) if data['ratings'] else 0
        result.append({'helper_id': hid, 'answered': data['answered'], 'avg_rating': avg, 'rated_count': data['rated_count']})
    result.sort(key=lambda x: x['answered'], reverse=True)
    return result

def delete_ticket(ticket_id):
    return tickets.remove(f"ticket_{ticket_id}")