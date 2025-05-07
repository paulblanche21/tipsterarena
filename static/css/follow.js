// Add loading and error styles
const styles = `
    .loading {
        text-align: center;
        padding: 20px;
        color: var(--gray-600);
    }
    
    .error-message {
        text-align: center;
        padding: 20px;
        color: var(--red-accent);
    }
    
    .retry-btn {
        margin-top: 10px;
        padding: 8px 16px;
        background: linear-gradient(45deg, var(--red-accent), var(--red-dark));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        border: 1px solid var(--red-accent);
        border-radius: 20px;
        cursor: pointer;
    }
    
    .retry-btn:hover {
        background: var(--red-dark);
        color: white;
        -webkit-text-fill-color: white;
    }
    
    .no-suggestions {
        text-align: center;
        padding: 20px;
        color: var(--gray-600);
    }

    .suggested-user-card .user-stats strong {
        background: linear-gradient(45deg, var(--black), var(--gray-800));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
`;

// ... rest of the code ... 