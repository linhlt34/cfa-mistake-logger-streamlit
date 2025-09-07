import streamlit as st
import pandas as pd
import os
import re
import random
from datetime import datetime

# Basic page configuration
st.set_page_config(page_title="Mistake Logger", layout="wide")

# --- CONFIGURATION & CONSTANTS ---
CSV_FILENAME = 'mistake_log.csv'

REQUIRED_COLUMNS = [
    'Category', 'Question Number', 'Result', 'Question Text', 'Error Type', 
    'Confidence Level', 'Time Spent', 'Difficulty Level', 'Notes', 'Timestamp'
]

MAIN_VALIDATION_FIELDS = ['Category', 'Question Number', 'Result', 'Question Text']

ERROR_TYPES = ["❌ Misread the question", "🔄 Wrong formula/concept", "⚠️ Calculation error", "❓ Uncertain"]

PARSING_RULES = {
    'Category': [
        # CFA specific patterns - most common first
        r"Application of the Code and Standards: Level II",  # Exact match for most common
        r"([A-Z][a-zA-Z\s:]+Level\s+[IVX]+)",  # General pattern for levels
        r"Review Category[:\s]+(.*?)(?=\n|Question)",
        r"Done Practicing\s*([A-Z][a-zA-Z\s]+?)(?=\s*Question|\s*\d+\s+of\s+\d+|\n|$)",
        # Extract category from end of text (common pattern in CFA questions)
        r"\n\s*([A-Z][a-zA-Z\s]+?)\s*\n\s*demonstrate the use",
        r"^(.*?)\n"
    ],
    'Question Number': [
        # CFA specific patterns - most common first
        r"Question\s+(\d+\s+of\s+\d+)",  # Standard "Question 1 of 1" format
        r"Question[:\s]+(\d+ of \d+)",
        r"(\d+\s+of\s+\d+)",  # Just the numbers part
    ],
    'Result': [
        # CFA specific patterns - most common first
        r"Your result is (\w+)\.",
        r"✓.*?(Correct)",  # Pattern for checkmark + Correct - capture "Correct"
        r"\b(Correct|Incorrect)\b",
        r"Correct Answer.*?Your Answer.*?([A-Z])\s*✓",  # Extract when answer is marked with checkmark
    ],
    'Question Text': [
        # CFA specific patterns - extract the actual question content
        r"Question\s*\n(.*?)(?=\s*A\.\s*$|\s*A\.\s*\n|\s*Solution)",  # Question followed by A. or Solution
        r"Question\s*\n\s*(.*?)(?=\s*Did.*violate)",  # For CFA ethics questions ending with "Did X violate"
        r"Question\s*\n(.*?)(?=\s*A\.|Solution)",  # General pattern
        r"(?:^|\n)\s*Question\s*\n(.*?)(?=\nSolution|\nA\.)",
        r"Question\s+(.*?)(?=\nA\.|\nSolution)",
        # Extract text between Question and A./Solution with flexible whitespace
        r"Question\s+(.*?)(?=\s*A\.\s*lower|\s*Solution)"
    ],
    'Confidence Level': [
        r"Confidence Level:\s*([^\n\r]*?)(?=\n|$|Continue)",
        r"Confidence Level:[^\n]*?\n([^\n\r]*?)(?=\n|$|Continue)"
    ],
    'Time Spent': [
        # CFA specific patterns - most common first
        r"Total:\s*(\d{2}:\d{2})",  # Extract from "Total: 00:03"
        r"This Question:\s*(\d{2}:\d{2})",  # Extract time from "This Question:01:36" format
        r"Time Spent:\s*(\d+ secs?)",  # Extract "3 secs"
        r"Time Spent:\s*([^\n]*?)(?=\n|$)"
    ],
    'Difficulty Level': [
        r"Difficulty Level:\s*([^\n]*?)(?=\n|$)"
    ]
}
# --- END OF CONFIGURATION ---

# --- Logic Functions ---
def parse_text(raw_text):
    """Parses raw text based on a configurable set of rules."""
    if not raw_text or not raw_text.strip():
        return None

    parsed_data = {}
    
    for field, patterns in PARSING_RULES.items():
        found = False
        for pattern in patterns:
            # Use appropriate flags based on the field type
            flags = re.IGNORECASE | re.DOTALL | re.MULTILINE
            match = re.search(pattern, raw_text, flags)
            if match:
                # Handle patterns with or without capturing groups
                if match.groups():
                    value = match.group(1).strip()
                else:
                    value = match.group(0).strip()
                
                # Special handling for different fields
                if field == 'Result':
                    value = value.capitalize()
                elif field == 'Time Spent':
                    # If it's already in seconds format, keep it
                    if 'sec' in value.lower():
                        pass  # Keep as is
                    elif ':' in value:
                        # Convert MM:SS format to "M mins SS secs" only if it's long enough to warrant it
                        try:
                            time_parts = value.split(':')
                            if len(time_parts) == 2:
                                minutes = int(time_parts[0])
                                seconds = int(time_parts[1])
                                if 0 <= minutes <= 999 and 0 <= seconds <= 59:
                                    # If less than 1 minute, just show seconds
                                    if minutes == 0:
                                        value = f"{seconds} secs"
                                    else:
                                        value = f"{minutes} mins {seconds} secs"
                        except (ValueError, IndexError):
                            pass  # Keep original format if conversion fails
                
                parsed_data[field] = value
                found = True
                break  # Stop when first match is found
        
        if not found:
            parsed_data[field] = ""
            
    return parsed_data

def save_to_csv(data):
    """Saves data to a CSV file."""
    # Add timestamp at the end
    data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Clean text fields to prevent CSV corruption
    def clean_text_field(text):
        """Clean text field for safe CSV storage."""
        if not text:
            return ''
        # Replace newlines with spaces
        text = re.sub(r'\r?\n', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    notes = clean_text_field(data.get('Notes', ''))
    question_text = clean_text_field(data.get('Question Text', ''))
    
    # Ensure proper column order with cleaned data
    ordered_data = {
        'Category': clean_text_field(data.get('Category', '')),
        'Question Number': clean_text_field(data.get('Question Number', '')),
        'Result': clean_text_field(data.get('Result', '')),
        'Question Text': question_text,
        'Error Type': clean_text_field(data.get('Error Type', '')),
        'Confidence Level': clean_text_field(data.get('Confidence Level', '')),
        'Time Spent': clean_text_field(data.get('Time Spent', '')),
        'Difficulty Level': clean_text_field(data.get('Difficulty Level', '')),
        'Notes': notes,
        'Timestamp': data.get('Timestamp', '')
    }
    
    df_new_row = pd.DataFrame([ordered_data])
    
    # Atomic CSV write to prevent race conditions
    import threading
    if not hasattr(save_to_csv, '_lock'):
        save_to_csv._lock = threading.Lock()
    
    with save_to_csv._lock:
        file_exists = os.path.exists(CSV_FILENAME)
        df_new_row.to_csv(CSV_FILENAME, mode='a', header=not file_exists, index=False, encoding='utf-8-sig', quoting=1)

def is_valid_data(data):
    """Check if parsed data contains valid information."""
    if not data:
        return False
    
    # Require essential fields: Category and Result at minimum
    # Question Text is preferred but not mandatory if we have other key data
    essential_fields = ['Category', 'Result']
    
    # All essential fields must have non-empty data
    for field in essential_fields:
        if field not in data or not data[field].strip():
            return False
    
    # If we have Question Number, that's also a strong indicator of valid data
    if data.get('Question Number', '').strip():
        return True
        
    # If we have Question Text, that's good too
    if data.get('Question Text', '').strip():
        return True
        
    # If we have Category and Result, accept it (user can manually add details)
    return True

def auto_save_and_clear(error_type, notes=""):
    """Save data with specified error type, clear the state, and rerun."""
    parsed_data = st.session_state.get("parsed_data")
    
    if parsed_data and error_type:
        parsed_data_copy = parsed_data.copy()
        
        # Treat "Uncertain" as a regular error type - don't modify Result
        # Keep the original Result (Correct/Incorrect) and just set Error Type
        parsed_data_copy['Error Type'] = clean_error_type_for_csv(error_type)
        parsed_data_copy['Notes'] = notes
        save_to_csv(parsed_data_copy)
        
        # Cập nhật session state để reset giao diện với bounds checking
        st.session_state.saved_successfully = True
        st.session_state.text_input_key = (st.session_state.text_input_key + 1) % 1000
        st.session_state.notes_input_key = (st.session_state.notes_input_key + 1) % 1000
        st.session_state.parsed_data = None
        
        st.rerun()

def clean_error_type_for_csv(error_type):
    """Remove icons from error types for CSV export."""
    if not error_type:
        return error_type
    
    # Remove common icons from error types
    cleaned = error_type.replace("❌ ", "").replace("🔄 ", "").replace("⚠️ ", "").replace("❓ ", "")
    return cleaned

def read_csv_safe(filepath):
    """
    Safely read CSV, ensuring all required columns exist.
    Prioritizes data integrity over attempting to read corrupted files.
    """
    required_columns = REQUIRED_COLUMNS
    
    try:
        # Đọc file với multiple encoding attempts để handle BOM issues
        try:
            df = pd.read_csv(filepath, encoding='utf-8-sig')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(filepath, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding='latin-1')
    except pd.errors.ParserError:
        # Nếu có lỗi phân tích (ví dụ: số cột không nhất quán),
        # thử lại bằng cách bỏ qua các dòng gây lỗi.
        st.warning("⚠️ Some lines in the CSV file were malformed and have been skipped.")
        try:
            df = pd.read_csv(filepath, on_bad_lines='skip', encoding='utf-8-sig')
        except Exception as e:
            st.error(f"The CSV file is severely corrupted and could not be read. Error: {e}")
            return None
    except Exception as e:
        st.error(f"An unexpected error occurred while reading the CSV file: {e}")
        return None

    # Sau khi đã đọc thành công, đảm bảo tất cả các cột cần thiết đều tồn tại
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''  # Thêm các cột bị thiếu với giá trị trống
    
    # Fix NaN values và data types để tương thích với st.dataframe
    df = df[required_columns].copy()
    
    # Convert all columns to string and replace NaN with empty string
    for col in required_columns:
        df[col] = df[col].fillna('').astype(str)
    
    return df


def export_csv():
    """Export the current CSV data with a date-based filename."""
    if os.path.exists(CSV_FILENAME):
        df = read_csv_safe(CSV_FILENAME)
        if df is not None and not df.empty:
            # Clean error types for export (remove icons)
            df_export = df.copy()
            df_export['Error Type'] = df_export['Error Type'].apply(clean_error_type_for_csv)
            
            # Ensure all text fields are properly encoded for Excel
            text_columns = ['Category', 'Question Text', 'Error Type', 'Notes', 'Confidence Level', 'Difficulty Level']
            for col in text_columns:
                if col in df_export.columns:
                    # Normalize Unicode characters and ensure proper encoding
                    df_export[col] = df_export[col].astype(str).apply(
                        lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') if x and x != 'nan' else ''
                    )
            
            date_str = datetime.now().strftime("%m%d")
            filename = f"mistake_log_{date_str}.csv"
            
            # Use UTF-8 with BOM for Excel compatibility and quote all text fields
            csv_data = df_export.to_csv(
                index=False, 
                encoding='utf-8-sig',  # BOM helps Excel recognize UTF-8
                quoting=1,  # Quote all non-numeric fields
                escapechar='\\',  # Proper escaping
                lineterminator='\n'  # Standard line endings
            )
            
            return csv_data, filename
    return None, None

def load_old_log(uploaded_file):
    """Load old log file and merge with current data, preventing duplicates."""
    if uploaded_file is not None:
        try:
            # Read uploaded file
            old_df = pd.read_csv(uploaded_file)
            
            # Ensure all required columns exist in old data
            required_columns = REQUIRED_COLUMNS
            
            for col in required_columns:
                if col not in old_df.columns:
                    old_df[col] = ''  # Add missing columns with empty values
            
            # Reorder columns
            old_df = old_df[required_columns]
            
            if os.path.exists(CSV_FILENAME):
                current_df = read_csv_safe(CSV_FILENAME)
                if current_df is not None:
                    # Append current data to old data
                    combined_df = pd.concat([current_df, old_df], ignore_index=True)
                    
                    # Remove duplicates based ONLY on Timestamp, keeping the last entry
                    # 'last' ensures that the data from the uploaded file (old_df) takes precedence
                    combined_df = combined_df.drop_duplicates(subset=['Timestamp'], keep='last')
                else:
                    combined_df = old_df
            else:
                combined_df = old_df
            
            # Save the combined data
            combined_df.to_csv(CSV_FILENAME, index=False, encoding='utf-8-sig', quoting=1)
            return True
        except Exception as e:
            st.error(f"Error loading file: {e}")
            return False
    return False

def delete_selected_mistakes(selected_indices):
    """Delete selected mistakes from the CSV file."""
    if not selected_indices or not os.path.exists(CSV_FILENAME):
        return False
    
    try:
        df = read_csv_safe(CSV_FILENAME)
        if df is None or df.empty:
            return False
        
        # Remove selected rows (indices are from the display, need to map to actual dataframe)
        df_filtered = df.drop(selected_indices).reset_index(drop=True)
        
        # Save the updated dataframe
        df_filtered.to_csv(CSV_FILENAME, index=False, encoding='utf-8-sig', quoting=1)
        return True
    except Exception as e:
        st.error(f"Error deleting mistakes: {e}")
        return False

def process_uploaded_log():
    """Handles single or multiple uploaded files with data protection."""
    
    # KIỂM TRA DỮ LIỆU ĐANG CHỜ (vẫn giữ nguyên)
    if st.session_state.get("parsed_data"):
        st.warning("⚠️ Please save your current entry before loading old logs.")
        # Cannot set uploader_key to None due to Streamlit restrictions
        return
        
    # Lấy danh sách các file đã tải lên
    uploaded_files = st.session_state.get("uploader_key")
    
    if uploaded_files:
        # Check if we already processed these files to avoid reprocessing
        if not st.session_state.get("files_processed", False):
            success_count = 0
            # Duyệt qua từng file trong danh sách và xử lý
            for uploaded_file in uploaded_files:
                if load_old_log(uploaded_file):
                    success_count += 1
            
            # Hiển thị thông báo tổng kết sau khi xử lý xong tất cả các file
            if success_count > 0:
                st.success(f"Successfully loaded and merged {success_count} file(s)!")
            
            # Mark files as processed to avoid reprocessing
            st.session_state.files_processed = True
    else:
        # Reset processed flag when no files are uploaded
        st.session_state.files_processed = False

# --- Initialize Session State ---
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = None
if 'saved_successfully' not in st.session_state:
    st.session_state.saved_successfully = False
if 'text_input_key' not in st.session_state:
    st.session_state.text_input_key = 0
if 'notes_input_key' not in st.session_state:
    st.session_state.notes_input_key = 0
if 'files_processed' not in st.session_state:
    st.session_state.files_processed = False
if 'selected_for_deletion' not in st.session_state:
    st.session_state.selected_for_deletion = []
if 'show_delete_mode' not in st.session_state:
    st.session_state.show_delete_mode = False

# --- User Interface ---
st.title("✍️ Mistake Logger")
st.markdown("Paste the entire content of the question into the box below.")

# Success message
if st.session_state.saved_successfully:
    st.success("✅ Saved successfully! Ready for the next question.")
    st.session_state.saved_successfully = False

# Large text input area
raw_text_input = st.text_area(
    "**Paste your content here:**",
    height=300,
    key=f"text_input_{st.session_state.text_input_key}"
)

# If the user has entered something and we don't already have valid parsed data
if raw_text_input and not st.session_state.get("parsed_data"):
    st.session_state.parsed_data = parse_text(raw_text_input)

# KIỂM TRA TÍNH HỢP LỆ CỦA DỮ LIỆU và chỉ hiển thị Notes + buttons nếu hợp lệ
if st.session_state.parsed_data and is_valid_data(st.session_state.parsed_data):
    # Nếu dữ liệu hợp lệ, hiển thị Notes và các nút bấm
    
    # Notes input field - chỉ hiển thị khi dữ liệu hợp lệ
    notes_input = st.text_area(
        "**Notes (Optional):**",
        height=100,
        placeholder="Add any important notes or observations here...",
        key=f"notes_input_{st.session_state.notes_input_key}"
    )
    
    st.markdown("**Please select the error type (will save automatically):**")
    
    # Tạo các nút bấm và gán hành động
    col1, col2, col3, col4 = st.columns(4)
    
    buttons = {
        col1: ERROR_TYPES[0],
        col2: ERROR_TYPES[1],
        col3: ERROR_TYPES[2],
        col4: ERROR_TYPES[3],
    }
    
    for col, error_type in buttons.items():
        with col:
            if st.button(error_type):
                # Lấy notes từ session state để đảm bảo giá trị mới nhất
                current_notes = st.session_state.get(f"notes_input_{st.session_state.notes_input_key}", "")
                auto_save_and_clear(error_type, current_notes)
                
elif raw_text_input:
    # Nếu có text nhập vào nhưng phân tích không hợp lệ
    st.warning("⚠️ Không thể tự động phân tích văn bản. Vui lòng kiểm tra lại định dạng nội dung bạn đã dán.")
    # Hiển thị dữ liệu đã phân tích để người dùng kiểm tra
    if st.session_state.parsed_data:
        st.subheader("🔍 Kết quả phân tích:")
        st.json(st.session_state.parsed_data)

# --- Display Log ---
st.markdown("---")
st.subheader("📜 Logged Mistake History")

# Export and Load buttons
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button("📥 Export CSV"):
        csv_data, filename = export_csv()
        if csv_data and filename:
            # Provide two download options
            col_csv, col_excel = st.columns(2)
            
            with col_csv:
                st.download_button(
                    label="📄 Download CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    help="Standard CSV - works in all programs"
                )
            
            with col_excel:
                # Create Excel-optimized version
                excel_filename = filename.replace('.csv', '_excel.csv')
                st.download_button(
                    label="📊 Download for Excel",
                    data=csv_data,
                    file_name=excel_filename,
                    mime="application/vnd.ms-excel",
                    help="Optimized for Microsoft Excel with Vietnamese text support"
                )
        else:
            st.warning("No valid data to export")

with col2:
    uploaded_files = st.file_uploader(
        "📤 Load & Merge Old Logs", 
        type=['csv'],
        help="You can now upload multiple CSV files at once.",
        key="uploader_key",  # Gán key để truy cập trong session_state
        on_change=process_uploaded_log,  # Tự động gọi hàm khi có file
        # THÊM DÒNG NÀY ĐỂ CHO PHÉP TẢI LÊN NHIỀU FILE
        accept_multiple_files=True
    )

with col3:
    if st.button("🗑️ Delete Mode"):
        st.session_state.show_delete_mode = not st.session_state.show_delete_mode
        if not st.session_state.show_delete_mode:
            st.session_state.selected_for_deletion = []

with col4:
    # Placeholder for delete button - will be shown after selections are processed
    delete_button_placeholder = st.empty()

# Display the log
if os.path.exists(CSV_FILENAME):
    df_log = read_csv_safe(CSV_FILENAME)
    if df_log is not None and len(df_log) > 0:
        # Display the last 10 rows, reversed to show the latest on top
        display_df = df_log.tail(10).iloc[::-1].reset_index(drop=False)
        display_indices = display_df['index'].tolist()  # Get original indices
        display_df_clean = display_df.drop('index', axis=1)  # Remove index column from display
        
        # Force clear any potential caching issues
        st.write(f"Found {len(df_log)} mistake(s) in log:")
        
        if st.session_state.show_delete_mode:
            st.warning("🗑️ Delete Mode: Select rows to delete, then click 'Delete Selected'")
            
            # Simple selection checkboxes in a clean row
            st.markdown("**Select rows:**")
            cols = st.columns(len(display_df_clean) if len(display_df_clean) <= 5 else 5)
            
            for i, (idx, row) in enumerate(display_df_clean.iterrows()):
                original_idx = display_indices[i]
                col_index = i % 5  # Max 5 per row
                
                with cols[col_index]:
                    is_selected = st.checkbox(
                        f"Row {i+1}",
                        value=original_idx in st.session_state.selected_for_deletion,
                        key=f"delete_checkbox_{original_idx}"
                    )
                    
                    # Update selection state
                    if is_selected and original_idx not in st.session_state.selected_for_deletion:
                        st.session_state.selected_for_deletion.append(original_idx)
                    elif not is_selected and original_idx in st.session_state.selected_for_deletion:
                        st.session_state.selected_for_deletion.remove(original_idx)
            
            # Add selection status to table
            display_with_status = display_df_clean.copy()
            status_column = []
            for i, (idx, row) in enumerate(display_df_clean.iterrows()):
                original_idx = display_indices[i]
                status = "🔴 DELETE" if original_idx in st.session_state.selected_for_deletion else ""
                status_column.append(status)
            
            display_with_status.insert(0, "Status", status_column)
            
            # Display clean single table
            st.dataframe(display_with_status, width='stretch', hide_index=True)
            
            # Show selection count and delete button after processing selections
            if st.session_state.selected_for_deletion:
                st.error(f"⚠️ {len(st.session_state.selected_for_deletion)} row(s) will be deleted")
            
            # Now that selections are processed, show the delete button using the placeholder
            with delete_button_placeholder.container():
                # Check if there are any items selected
                has_selections = len(st.session_state.selected_for_deletion) > 0
                
                if has_selections:
                    if st.button("❌ Delete Selected", type="primary", key="delete_btn"):
                        if delete_selected_mistakes(st.session_state.selected_for_deletion):
                            st.success(f"Deleted {len(st.session_state.selected_for_deletion)} mistake(s)!")
                            st.session_state.selected_for_deletion = []
                            st.session_state.show_delete_mode = False
                            st.rerun()
                        else:
                            st.error("Failed to delete selected mistakes.")
                else:
                    # Show disabled button with helper text
                    st.button("❌ Delete Selected", type="primary", disabled=True, key="delete_btn_disabled")
                    st.caption("Select items above to enable deletion")
        else:
            # Normal display mode
            # Clear the delete button placeholder when not in delete mode
            with delete_button_placeholder.container():
                pass  # Empty container
            
            try:
                st.dataframe(display_df_clean, width='stretch')
            except Exception as e:
                st.error(f"Error displaying dataframe: {e}")
                # Fallback to table display
                st.table(display_df_clean)
    elif df_log is not None:
        st.info("Mistake log file exists but contains no data.")
        # Clear the delete button placeholder when no data
        with delete_button_placeholder.container():
            pass  # Empty container
    else:
        st.error("Error reading the mistake log file. Please check the file format.")
        # Clear the delete button placeholder on error
        with delete_button_placeholder.container():
            pass  # Empty container
else:
    st.info("No mistakes have been logged yet.")
    # Clear the delete button placeholder when no file exists
    if 'delete_button_placeholder' in locals():
        with delete_button_placeholder.container():
            pass  # Empty container