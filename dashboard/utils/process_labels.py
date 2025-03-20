from textwrap import wrap as text_wrap

def format_labels(labels, wrap=None, truncate=None, separator="..."):
    """
    Formats labels by applying word wrapping and/or truncation.
    
    Parameters:
        labels (list): List of text labels to format.
        wrap (int, optional): Max length before wrapping text into new lines.
        truncate (int, optional): Max length before truncating text.
        separator (str, optional): Separator for truncated text, default "...".
        
    Returns:
        tuple: (formatted_labels, hover_labels)
            - formatted_labels: Labels modified for display.
            - hover_labels: Original labels for hover (useful when truncated).
    """
    formatted_labels = []
    hover_labels = []
    
    for label in labels:
        original_label = label 

        if truncate and len(label) > truncate:
            words = label.split()
            if len(words) == 1: 
                label = label[:truncate - len(separator)] + separator
            else:
                first_part = words[0][:truncate // 2]
                last_part = words[-1][-truncate // 2:]
                label = f"{first_part}{separator}{last_part}"
        
        elif wrap and len(label) > wrap:
            label = "<br>".join(text_wrap(label, wrap))

        formatted_labels.append(label)
        hover_labels.append(original_label)  
    
    return formatted_labels, hover_labels

