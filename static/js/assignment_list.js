document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const table = document.getElementById('assignmentsTable');
    const rows = table.querySelectorAll('tbody .assignment-row');
    const emptyState = document.getElementById('emptyState');

    // Search functionality
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        let visibleRows = 0;

        rows.forEach(row => {
            const title = row.dataset.title;
            const author = row.dataset.author;
            const shouldShow = title.includes(searchTerm) || author.includes(searchTerm);
            
            if (shouldShow) {
                row.style.display = '';
                visibleRows++;
                highlightSearchTerm(row, searchTerm);
            } else {
                row.style.display = 'none';
            }
        });

        // Show/hide empty state
        if (emptyState) {
            emptyState.style.display = visibleRows === 0 ? '' : 'none';
        }
    });

    // Filter functionality
    const filterButtons = document.querySelectorAll('#assignmentTabs button');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.id.replace('-tab', '');
            filterAssignments(filter);
        });
    });

    function filterAssignments(filter) {
        rows.forEach(row => {
            let shouldShow = true;
            
            switch(filter) {
                case 'active':
                    shouldShow = !row.classList.contains('overdue-row');
                    break;
                case 'overdue':
                    shouldShow = row.classList.contains('overdue-row');
                    break;
                case 'all':
                default:
                    shouldShow = true;
                    break;
            }
            
            row.style.display = shouldShow ? '' : 'none';
        });
    }

    // Sorting functionality
    const sortableHeaders = document.querySelectorAll('.sortable');
    let sortDirection = {};

    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.dataset.column;
            const currentDirection = sortDirection[column] || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            sortDirection[column] = newDirection;
            
            sortTable(column, newDirection);
            updateSortIcon(this, newDirection);
        });
    });

    function sortTable(column, direction) {
        const tbody = table.querySelector('tbody');
        const sortedRows = Array.from(rows).sort((a, b) => {
            let aVal = '', bVal = '';
            
            switch(column) {
                case 'title':
                    aVal = a.dataset.title;
                    bVal = b.dataset.title;
                    break;
                case 'author':
                    aVal = a.dataset.author;
                    bVal = b.dataset.author;
                    break;
                case 'due-date':
                case 'created':
                    aVal = new Date(a.dataset[column.replace('-', '')]);
                    bVal = new Date(b.dataset[column.replace('-', '')]);
                    break;
            }
            
            if (aVal < bVal) return direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return direction === 'asc' ? 1 : -1;
            return 0;
        });

        // Remove existing rows and add sorted ones
        rows.forEach(row => row.remove());
        sortedRows.forEach(row => tbody.appendChild(row));
    }

    function updateSortIcon(header, direction) {
        // Reset all sort icons
        sortableHeaders.forEach(h => {
            const icon = h.querySelector('.fa-sort, .fa-sort-up, .fa-sort-down');
            icon.className = icon.className.replace(/fa-sort-(up|down)/, 'fa-sort');
        });
        
        // Update clicked header icon
        const icon = header.querySelector('.fas:last-child');
        icon.className = icon.className.replace('fa-sort', `fa-sort-${direction === 'asc' ? 'up' : 'down'}`);
    }

    function highlightSearchTerm(row, searchTerm) {
        if (!searchTerm) return;
        
        const titleElement = row.querySelector('.assignment-title');
        const originalText = titleElement.textContent;
        const highlightedText = originalText.replace(
            new RegExp(searchTerm, 'gi'),
            match => `<span class="search-highlight">${match}</span>`
        );
        titleElement.innerHTML = highlightedText;
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Delete confirmation function
function confirmDelete(assignmentId, assignmentTitle) {
    document.getElementById('assignmentTitle').textContent = assignmentTitle;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
    
    document.getElementById('confirmDeleteBtn').onclick = function() {
        // Add your delete logic here - could be a form submission or AJAX call
        window.location.href = `/assignments/${assignmentId}/delete/`;
    };
}