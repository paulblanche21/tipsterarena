async function fetchGolfEvents(state = 'pre', tourId = null) {
    try {
        const url = new URL('/api/golf-events/', window.location.origin);
        url.searchParams.append('state', state);
        if (tourId) {
            url.searchParams.append('tour_id', tourId);
        }

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching golf events:', error);
        return [];
    }
} 