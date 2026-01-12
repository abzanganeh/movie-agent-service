// Tab switching
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Activate selected button
    event.target.classList.add('active');
}

// Chat functionality
let chatMessages = [];

function addChatMessage(role, content, metadata = null) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let html = `<div class="message-header">${role === 'user' ? 'You' : 'Assistant'}</div>`;
    
    // Check if this is a quiz response or quiz feedback
    if (metadata && metadata.quiz_data) {
        html += renderQuizContent(metadata.quiz_data, content);
    } else if (content && (content.includes('Correct') || content.includes('Incorrect') ||
                          content.includes('Great job') || content.includes("Let's try"))) {
        // Show feedback even without quiz_data (feedback-only message)
        html += renderQuizContent(null, content);
    } else if (content && (content.includes('Highest Rated') || 
                          content.includes('Top') && content.includes('Rated') || 
                          content.includes('Average Rating') ||
                          content.includes('Genre Distribution') ||
                          content.includes('Lowest Rated'))) {
        html += renderStatisticsContent(content);
    } else {
        html += `<div class="message-content">${escapeHtml(content)}</div>`;
    }
    
    if (metadata) {
        html += '<div class="message-meta">';
        
        if (metadata.movies && metadata.movies.length > 0) {
            html += '<div class="movies-list">';
            html += '<strong>Movies:</strong> ';
            metadata.movies.forEach(movie => {
                html += `<span class="movie-tag">${movie}</span>`;
            });
            html += '</div>';
        }
        
        if (metadata.tools_used && metadata.tools_used.length > 0) {
            html += `<div><strong>Tools:</strong> ${metadata.tools_used.join(', ')}</div>`;
        }
        
        if (metadata.latency_ms) {
            html += `<div><strong>Latency:</strong> ${metadata.latency_ms}ms`;
            if (metadata.llm_latency_ms) {
                html += ` (LLM: ${metadata.llm_latency_ms}ms`;
                if (metadata.tool_latency_ms) {
                    html += `, Tools: ${metadata.tool_latency_ms}ms`;
                }
                html += ')';
            }
            html += '</div>';
        }
        
        html += '</div>';
    }
    
    messageDiv.innerHTML = html;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function renderQuizContent(quizData, answerText) {
    let html = '<div class="quiz-container">';
    
    // If no quizData but we have answerText with feedback, show it
    if (!quizData && answerText) {
        const isFeedback = answerText.includes('Correct') || answerText.includes('Incorrect');
        if (isFeedback) {
            const isCorrect = answerText.includes('Correct');
            const feedbackClass = isCorrect ? 'quiz-feedback correct' : 'quiz-feedback incorrect';
            html += `<div class="${feedbackClass}">${escapeHtml(answerText)}</div>`;
            html += '</div>';
            return html;
        }
    }
    
    // Quiz complete
    if (quizData && quizData.quiz_complete) {
        html += `
            <div class="quiz-complete">
                <h3>Quiz Complete!</h3>
                <div class="quiz-score">
                    <strong>Your Score:</strong> ${quizData.score} / ${quizData.total}
                </div>
                <div class="quiz-topic">Topic: ${escapeHtml(quizData.topic)}</div>
            </div>
        `;
    }
    // Active quiz question
    else if (quizData && quizData.quiz_active && quizData.question) {
        html += `
            <div class="quiz-header">
                <h3>Movie Quiz: ${escapeHtml(quizData.topic || 'movies')}</h3>
                <div class="quiz-progress">
                    Question ${quizData.progress.current} of ${quizData.progress.total}
                </div>
            </div>
            <div class="quiz-question">
                <div class="question-text">${escapeHtml(quizData.question)}</div>
                <div class="question-options">
        `;
        
        quizData.options.forEach((option, index) => {
            // Escape option for use in onclick attribute (handle quotes)
            const escapedOption = String(option).replace(/'/g, "\\'").replace(/"/g, '&quot;');
            html += `
                <div class="quiz-option" onclick="answerQuizQuestion('${escapedOption}', ${index + 1})">
                    <strong>${index + 1}.</strong> ${escapeHtml(option)}
                </div>
            `;
        });
        
        html += `
                </div>
                <div class="quiz-hint">
                    Answer with the number (1, 2, 3) or the year
                </div>
            </div>
        `;
    }
    
    // Add answer text if provided (for feedback or completion messages)
    if (answerText) {
        // Show answer text if:
        // 1. No quiz data (feedback only)
        // 2. Quiz is complete
        // 3. Quiz is not active
        if (!quizData || (quizData && (quizData.quiz_complete || !quizData.quiz_active))) {
            html += `<div class="message-content">${escapeHtml(answerText)}</div>`;
        }
    }
    
    html += '</div>';
    return html;
}

function renderStatisticsContent(content) {
    // Parse statistics content and render beautifully
    let html = '<div class="statistics-container">';
    
    // Check for different statistics types
    // IMPORTANT: Check "Top X Highest Rated Movies:" FIRST because it contains "Highest Rated Movies:" as substring
    if (content.includes('Top') && content.includes('Highest Rated Movies:')) {
        html += '<div class="statistics-header">Top Rated Movies</div>';
        const topMatch = content.match(/Top (\d+) Highest Rated Movies:\n\n([\s\S]*)/);
        if (topMatch) {
            const [, count, moviesText] = topMatch;
            html += `<div class="statistics-subheader">Top ${count} Movies by Rating</div>`;
            const movies = moviesText.split('\n').filter(line => line.trim().match(/^\d+\./));
            html += '<div class="statistics-list">';
            movies.forEach(movie => {
                const match = movie.match(/(\d+)\.\s*(.+?)\s*\((\d+)\)\s*-\s*Rating:\s*([\d.]+)\/10/);
                if (match) {
                    const [, rank, title, year, rating] = match;
                    html += `
                        <div class="statistics-item">
                            <div class="statistics-rank">#${rank}</div>
                            <div class="statistics-content">
                                <div class="statistics-title">${escapeHtml(title)} (${year})</div>
                                <div class="statistics-rating">⭐ ${rating}/10</div>
                            </div>
                        </div>
                    `;
                }
            });
            html += '</div>';
        }
    } else if (content.includes('Highest Rated Movies:') && !content.includes('Top')) {
        // Single highest rated movie (not a list)
        html += '<div class="statistics-header">Highest Rated Movies</div>';
        const movieMatch = content.match(/Highest Rated Movies:\n\n([\s\S]*?)\n\nRating:/);
        if (movieMatch) {
            const movies = movieMatch[1].split('\n').filter(line => line.trim().startsWith('•'));
            html += '<div class="statistics-list">';
            movies.forEach(movie => {
                const match = movie.match(/•\s*(.+?)\s*\((\d+)\)\s*-\s*Rating:\s*([\d.]+)\/10/);
                if (match) {
                    const [, title, year, rating] = match;
                    html += `
                        <div class="statistics-item">
                            <div class="statistics-title">${escapeHtml(title)} (${year})</div>
                            <div class="statistics-rating">⭐ ${rating}/10</div>
                        </div>
                    `;
                }
            });
            html += '</div>';
            const ratingMatch = content.match(/Rating:\s*([\d.]+)\/10/);
            if (ratingMatch) {
                html += `<div class="statistics-summary">Highest Rating: ${ratingMatch[1]}/10</div>`;
            }
        }
    } else if (content.includes('Average Rating:')) {
        html += '<div class="statistics-header">Average Rating</div>';
        const match = content.match(/Average Rating:\s*([\d.]+)\/10\s*\(based on (\d+) movies\)/);
        if (match) {
            const [, avg, count] = match;
            html += `
                <div class="statistics-summary">
                    <div class="statistics-value">${avg}/10</div>
                    <div class="statistics-label">Based on ${count} movies</div>
                </div>
            `;
        }
    } else if (content.includes('Lowest Rated Movies:')) {
        html += '<div class="statistics-header">Lowest Rated Movies</div>';
        const movieMatch = content.match(/Lowest Rated Movies:\n\n([\s\S]*?)\n\nRating:/);
        if (movieMatch) {
            const movies = movieMatch[1].split('\n').filter(line => line.trim().startsWith('•'));
            html += '<div class="statistics-list">';
            movies.forEach(movie => {
                const match = movie.match(/•\s*(.+?)\s*\((\d+)\)\s*-\s*Rating:\s*([\d.]+)\/10/);
                if (match) {
                    const [, title, year, rating] = match;
                    html += `
                        <div class="statistics-item">
                            <div class="statistics-title">${escapeHtml(title)} (${year})</div>
                            <div class="statistics-rating">⭐ ${rating}/10</div>
                        </div>
                    `;
                }
            });
            html += '</div>';
        }
    } else if (content.includes('Genre Distribution:')) {
        html += '<div class="statistics-header">Genre Distribution</div>';
        const genreMatch = content.match(/Genre Distribution:\n\n([\s\S]*)/);
        if (genreMatch) {
            const genres = genreMatch[1].split('\n').filter(line => line.trim().startsWith('•'));
            html += '<div class="statistics-list">';
            genres.forEach(genre => {
                const match = genre.match(/•\s*(.+?):\s*(\d+)/);
                if (match) {
                    const [, name, count] = match;
                    html += `
                        <div class="statistics-item">
                            <div class="statistics-title">${escapeHtml(name)}</div>
                            <div class="statistics-count">${count} movies</div>
                        </div>
                    `;
                }
            });
            html += '</div>';
        }
    } else {
        // Fallback: render as plain text with formatting preserved
        html += `<div class="message-content">${escapeHtml(content).replace(/\n/g, '<br>')}</div>`;
    }
    
    html += '</div>';
    return html;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function answerQuizQuestion(answer, optionNumber) {
    // Send the answer as a chat message
    const input = document.getElementById('chat-input');
    input.value = answer; // Set the answer in the input
    sendChatMessage(); // Send it
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    
    if (!query) return;
    
    // Add user message
    addChatMessage('user', query);
    input.value = '';
    input.disabled = true;
    
    // Show loading
    const messagesDiv = document.getElementById('chat-messages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.id = 'loading-indicator';
    loadingDiv.textContent = 'Thinking...';
    messagesDiv.appendChild(loadingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });
        
        const data = await response.json();
        
        // Remove loading
        document.getElementById('loading-indicator').remove();
        
        if (response.ok) {
            addChatMessage('assistant', data.answer, {
                movies: data.movies || [],
                tools_used: data.tools_used || [],
                latency_ms: data.latency_ms,
                llm_latency_ms: data.llm_latency_ms,
                tool_latency_ms: data.tool_latency_ms,
                quiz_data: data.quiz_data || null,
            });
        } else {
            addChatMessage('assistant', `Error: ${data.error || 'Unknown error'}`, null);
        }
    } catch (error) {
        document.getElementById('loading-indicator').remove();
        addChatMessage('assistant', `Error: ${error.message}`, null);
    } finally {
        input.disabled = false;
        input.focus();
    }
}

// Image analysis functionality
function handleImageSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('image-preview');
        const previewImg = document.getElementById('preview-img');
        const uploadArea = document.getElementById('upload-area');
        
        previewImg.src = e.target.result;
        preview.style.display = 'block';
        uploadArea.style.display = 'none';
        
        // Clear previous results
        document.getElementById('image-results').innerHTML = '';
    };
    reader.readAsDataURL(file);
}

// Make upload area clickable
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const imageInput = document.getElementById('image-input');
    
    uploadArea.addEventListener('click', () => {
        imageInput.click();
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.background = '#f0f0f0';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.background = '#f9f9f9';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.background = '#f9f9f9';
        
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            imageInput.files = e.dataTransfer.files;
            handleImageSelect({ target: imageInput });
        }
    });
});

async function analyzeImage() {
    const imageInput = document.getElementById('image-input');
    const file = imageInput.files[0];
    
    if (!file) {
        alert('Please select an image first');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', file);
    
    const analyzeButton = document.querySelector('.analyze-button');
    analyzeButton.disabled = true;
    analyzeButton.textContent = 'Analyzing...';
    
    const resultsDiv = document.getElementById('image-results');
    resultsDiv.innerHTML = '<div class="loading">Analyzing poster...</div>';
    
    try {
        const response = await fetch('/poster', {
            method: 'POST',
            body: formData,
        });
        
        const data = await response.json();
        
        if (response.ok) {
            let html = '<div class="result-card">';
            html += '<div class="result-title">Analysis Results</div>';
            
            // Always show title field, even if None/Unknown
            html += `<div class="result-item">`;
            html += `<span class="result-label">Title:</span>`;
            html += `<span class="result-value">${data.title || 'Not identified'}</span>`;
            html += `</div>`;
            
            if (data.inferred_genres && data.inferred_genres.length > 0) {
                html += `<div class="result-item">`;
                html += `<span class="result-label">Genres:</span>`;
                data.inferred_genres.forEach(genre => {
                    html += `<span class="genre-tag">${genre}</span>`;
                });
                html += `</div>`;
            }
            
            if (data.mood) {
                html += `<div class="result-item">`;
                html += `<span class="result-label">Mood:</span>`;
                html += `<span class="result-value">${data.mood}</span>`;
                html += `</div>`;
            }
            
            if (data.confidence !== undefined) {
                html += `<div class="result-item">`;
                html += `<span class="result-label">Confidence:</span>`;
                html += `<span class="result-value">${(data.confidence * 100).toFixed(1)}%</span>`;
                html += `</div>`;
            }
            
            html += '</div>';
            resultsDiv.innerHTML = html;
        } else {
            resultsDiv.innerHTML = `<div class="error">Error: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    } finally {
        analyzeButton.disabled = false;
        analyzeButton.textContent = 'Analyze Poster';
    }
}

// Reset image preview
async function resetImagePreview() {
    // Clear poster state in session
    try {
        await fetch('/clear-poster', {
            method: 'POST',
        });
    } catch (error) {
        console.error('Error clearing poster state:', error);
    }
    
    // Reset file input
    const imageInput = document.getElementById('image-input');
    imageInput.value = '';
    
    // Show upload area, hide preview
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('image-preview').style.display = 'none';
    
    // Clear results
    document.getElementById('image-results').innerHTML = '';
    
    // Clear preview image src
    document.getElementById('preview-img').src = '';
}

// Reset configuration
async function resetConfig() {
    if (!confirm('Are you sure you want to reset the configuration? This will require setup again.')) {
        return;
    }
    
    try {
        const response = await fetch('/reset-config', {
            method: 'POST',
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Configuration reset. Redirecting to setup...');
            window.location.href = '/setup';
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

