function addComment(bookId) {
    fetch(`/api/books/${bookId}/comments`, {
        method: 'post',
        body: JSON.stringify({
            'content': document.getElementById('content').value
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then(data => {
        if (data) {
            const commentList = document.getElementById('comment-list');
            const newComment = `
                <li class="list-group-item">
                    <div class="d-flex align-items-start">
                        <img src="${data.user.avatar}" alt="Avatar" class="rounded-circle me-3"
                             style="width: 50px; height: 50px; object-fit: cover;">
                        <div>
                            <h6 class="fw-bold mb-1">${data.user.username}</h6>
                            <p class="mb-1">${data.content}</p>
                            <small class="text-muted">${new Date(data.created_at).toLocaleString()}</small>
                        </div>
                    </div>
                </li>
            `;
            commentList.insertAdjacentHTML('beforeend', newComment);
            document.getElementById('content').value = '';
        }
        location.reload();
    })
}