#!/usr/bin/env python3

import pandas as pd
import sys
import os
import re
from typing import List, Dict, Any
import argparse
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def normalize_phone(phone: str) -> str:
    """Normalize phone number to consistent format"""
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # If it starts with +1, keep it
    if cleaned.startswith('+1'):
        return cleaned
    
    # If it starts with 1 and has 11 digits, add +
    if cleaned.startswith('1') and len(cleaned) == 11:
        return '+' + cleaned
    
    # If it has 10 digits, add +1
    if len(cleaned) == 10:
        return '+1' + cleaned
    
    return phone  # Return original if can't normalize

def normalize_interests(interests: str) -> str:
    """Normalize dining interests to consistent format"""
    if not interests:
        return ""
    
    # Split by comma and clean up
    interest_list = [interest.strip() for interest in interests.split(',')]
    return ', '.join(interest_list)

def normalize_state(state: str) -> str:
    """Normalize state names"""
    if not state:
        return ""
    
    # Dictionary of state abbreviations to full names
    state_mapping = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
        'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
        'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
        'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
        'WI': 'Wisconsin', 'WY': 'Wyoming'
    }
    
    # If it's an abbreviation, convert to full name
    if state.upper() in state_mapping:
        return state_mapping[state.upper()]
    
    # Otherwise return as-is (already full name)
    return state.title()

def clean_diner_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Clean and normalize the diner data"""
    
    # Standardize column names to match our expected format
    column_mapping = {
        'First Name': 'first_name',
        'Last Name': 'last_name',
        'Seniority': 'seniority',
        'City': 'city',
        'State': 'state',
        'Address': 'address',
        'Dining Interests': 'dining_interests',
        'Email': 'email',
        'Phone': 'phone'
    }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Fill NaN values
    df = df.fillna('')
    
    diners = []
    skipped = []
    
    for index, row in df.iterrows():
        try:
            # Normalize phone number (required field)
            phone = normalize_phone(str(row.get('phone', '')))
            if not phone:
                skipped.append(f"Row {index + 1}: Missing phone number")
                continue
            
            diner = {
                'phone': phone,
                'first_name': str(row.get('first_name', '')).strip(),
                'last_name': str(row.get('last_name', '')).strip(),
                'seniority': str(row.get('seniority', '')).strip(),
                'city': str(row.get('city', '')).strip(),
                'state': normalize_state(str(row.get('state', '')).strip()),
                'address': str(row.get('address', '')).strip(),
                'dining_interests': normalize_interests(str(row.get('dining_interests', '')).strip()),
                'email': str(row.get('email', '')).strip().lower(),
                'consent_email': True,  # Default to True for challenge data
                'consent_sms': True     # Default to True for challenge data
            }
            
            diners.append(diner)
            
        except Exception as e:
            skipped.append(f"Row {index + 1}: Error processing - {str(e)}")
    
    if skipped:
        print(f"Skipped {len(skipped)} rows:")
        for skip in skipped[:10]:  # Show first 10 skipped rows
            print(f"  - {skip}")
        if len(skipped) > 10:
            print(f"  ... and {len(skipped) - 10} more")
    
    return diners

def import_to_supabase(diners: List[Dict[str, Any]]) -> bool:
    """Import diners to Supabase"""
    
    # Get Supabase credentials from environment
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Clear existing sample data first
        print("Clearing existing sample data...")
        result = supabase.table('diners').delete().neq('phone', 'xxx-xxx-xxxx').execute()
        
        # Insert diners in batches
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(diners), batch_size):
            batch = diners[i:i + batch_size]
            
            try:
                result = supabase.table('diners').upsert(batch).execute()
                total_inserted += len(batch)
                print(f"Inserted batch {i // batch_size + 1}: {len(batch)} diners (Total: {total_inserted})")
                
            except Exception as e:
                print(f"Error inserting batch {i // batch_size + 1}: {str(e)}")
                return False
        
        print(f"\n✅ Successfully imported {total_inserted} diners to Supabase!")
        return True
        
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        return False

def load_from_csv(file_path: str) -> pd.DataFrame:
    """Load data from CSV file"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"✅ Successfully loaded CSV with {encoding} encoding")
            return df
        except UnicodeDecodeError:
            continue
    
    raise ValueError(f"Could not read CSV file with any of these encodings: {encodings}")

def load_from_google_sheets(url: str) -> pd.DataFrame:
    """Load data from Google Sheets URL"""
    # Convert Google Sheets URL to CSV export URL
    if 'docs.google.com/spreadsheets' in url:
        # Extract the sheet ID
        sheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if sheet_id_match:
            sheet_id = sheet_id_match.group(1)
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            print(f"Converting to CSV URL: {csv_url}")
            df = pd.read_csv(csv_url)
            print(f"✅ Successfully loaded Google Sheets data")
            return df
    
    raise ValueError("Invalid Google Sheets URL format")

def main():
    parser = argparse.ArgumentParser(description='Import challenge diner data')
    parser.add_argument('--csv-file', help='Path to CSV file')
    parser.add_argument('--google-sheets-url', help='Google Sheets URL')
    parser.add_argument('--preview', action='store_true', help='Preview data without importing')
    
    args = parser.parse_args()
    
    if not args.csv_file and not args.google_sheets_url:
        # Use default Google Sheets URL from challenge
        args.google_sheets_url = "https://docs.google.com/spreadsheets/d/1dG5eQWpmBP7xEy_ku0zZ94dklbFTy9tq6-eANQwyMVI/edit?usp=sharing"
        print("Using default challenge Google Sheets URL")
    
    try:
        # Load data
        if args.csv_file:
            print(f"Loading data from CSV: {args.csv_file}")
            df = load_from_csv(args.csv_file)
        else:
            print(f"Loading data from Google Sheets: {args.google_sheets_url}")
            df = load_from_google_sheets(args.google_sheets_url)
        
        print(f"Loaded {len(df)} rows from source")
        print(f"Columns: {list(df.columns)}")
        
        # Clean and normalize data
        print("\nCleaning and normalizing data...")
        diners = clean_diner_data(df)
        
        print(f"Processed {len(diners)} valid diners")
        
        # Preview first few records
        if diners:
            print("\nSample data:")
            for i, diner in enumerate(diners[:3]):
                print(f"  {i+1}. {diner['first_name']} {diner['last_name']} - {diner['phone']} - {diner['city']}, {diner['state']}")
        
        if args.preview:
            print("\n📋 Preview mode - not importing to database")
            return
        
        # Import to Supabase
        print(f"\nImporting {len(diners)} diners to Supabase...")
        success = import_to_supabase(diners)
        
        if success:
            print("\n🎉 Import completed successfully!")
        else:
            print("\n❌ Import failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
