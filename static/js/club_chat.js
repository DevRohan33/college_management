
// import { 
//   initializeApp 
// } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";
// import { 
//   getDatabase, ref, push, set, onChildAdded, onValue, update, serverTimestamp, onDisconnect, remove
// } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-database.js";
// // Firebase Config
//     const { firebase, clubId, userId, username, displayName, clubDetailUrl, clubName } = window.chatConfig;

//     const firebaseConfig = firebase;
//     const CLUB_ID = clubId;
//     const USER_ID = userId;
//     const USERNAME = username;
//     const DISPLAY_NAME = displayName;
//     const app = initializeApp(firebaseConfig);
//     const db = getDatabase(app);




//     // DOM Elements
//     const chatForm = document.getElementById('chat-form');
//     const messageInput = document.getElementById('message-input');
//     const chatMessages = document.getElementById('chat-messages');
//     const charCount = document.getElementById('char-count');
//     const typingIndicator = document.getElementById('typing-indicator');
//     const emojiButton = document.getElementById('emoji-button');
//     const quickEmojiPanel = document.getElementById('quick-emoji-panel');
//     const attachButton = document.getElementById('attach-button');
//     const fileInput = document.getElementById('file-input');
//     const filePreview = document.getElementById('file-preview');
//     const previewContent = document.getElementById('preview-content');
//     const removeFileButton = document.getElementById('remove-file');
//     const emptyChat = document.getElementById('empty-chat');

//     let selectedFile = null;
//     let typingTimeout = null;

//     // Firebase References
//     const chatRef = ref(db, `clubs/${CLUB_ID}/chats`);
//     const typingRef = ref(db, `clubs/${CLUB_ID}/typing/${USER_ID}`);
//     const onlineRef = ref(db, `clubs/${CLUB_ID}/online/${USER_ID}`);

//     // Initialize
//     document.addEventListener('DOMContentLoaded', function() {
//       initializeChat();
//       setupEventListeners();
//       updateOnlinePresence();
//     });

//     function initializeChat() {
//       // Listen for new messages
//       onChildAdded(chatRef, (snapshot) => {
//         const data = snapshot.val();
//         const messageId = snapshot.key;
//         addMessageToChat(data, messageId);
//       });

//       // Listen for typing indicators
//       onValue(ref(db, `clubs/${CLUB_ID}/typing`), (snapshot) => {
//         const typingUsers = snapshot.val() || {};
//         updateTypingIndicator(typingUsers);
//       });

//       // Listen for online users
//       onValue(ref(db, `clubs/${CLUB_ID}/online`), (snapshot) => {
//         const onlineUsers = snapshot.val() || {};
//         updateOnlineCount(onlineUsers);
//       });
//     }

//     function setupEventListeners() {
//       // Chat form submission
//       chatForm.addEventListener('submit', function(e) {
//         e.preventDefault();
//         sendMessage();
//       });

//       // Character counter
//       messageInput.addEventListener('input', function() {
//         updateCharCount();
//         handleTyping();
//       });

//       // Emoji button
//       emojiButton.addEventListener('click', function() {
//         toggleQuickEmojiPanel();
//       });

//       // Quick emoji selection
//       document.querySelectorAll('.quick-emoji').forEach(btn => {
//         btn.addEventListener('click', function() {
//           const emoji = this.dataset.emoji;
//           messageInput.value += emoji;
//           messageInput.focus();
//           quickEmojiPanel.style.display = 'none';
//         });
//       });

//       // File attachment
//       attachButton.addEventListener('click', function() {
//         fileInput.click();
//       });

//       fileInput.addEventListener('change', function(e) {
//         const file = e.target.files[0];
//         if (file) {
//           selectedFile = file;
//           showFilePreview(file);
//         }
//       });

//       removeFileButton.addEventListener('click', function() {
//         selectedFile = null;
//         fileInput.value = '';
//         filePreview.style.display = 'none';
//       });

//       // Poll modal handlers
//       setupPollModal();

//       // Close emoji panel when clicking outside
//       document.addEventListener('click', function(e) {
//         if (!emojiButton.contains(e.target) && !quickEmojiPanel.contains(e.target)) {
//           quickEmojiPanel.style.display = 'none';
//         }
//       });

//       // Enter key to send message
//       messageInput.addEventListener('keypress', function(e) {
//         if (e.key === 'Enter' && !e.shiftKey) {
//           e.preventDefault();
//           sendMessage();
//         }
//       });
//     }

//     function updateCharCount() {
//       const count = messageInput.value.length;
//       charCount.textContent = `${count}/500`;
      
//       if (count > 400) {
//         charCount.className = 'char-counter danger';
//       } else if (count > 300) {
//         charCount.className = 'char-counter warning';
//       } else {
//         charCount.className = 'char-counter';
//       }
//     }

//     function handleTyping() {
//       // Clear previous timeout
//       if (typingTimeout) {
//         clearTimeout(typingTimeout);
//       }

//       // Set user as typing
//       set(typingRef, {
//         username: DISPLAY_NAME,
//         typing: true,
//         timestamp: Date.now()
//       });

//       // Stop typing after 2 seconds of inactivity
//       typingTimeout = setTimeout(() => {
//         remove(typingRef);
//       }, 2000);
//     }

//     function toggleQuickEmojiPanel() {
//       const isVisible = quickEmojiPanel.style.display === 'block';
//       quickEmojiPanel.style.display = isVisible ? 'none' : 'block';
//     }

//     function showFilePreview(file) {
//       const reader = new FileReader();
      
//       reader.onload = function(e) {
//         let previewHTML = '';
        
//         if (file.type.startsWith('image/')) {
//           previewHTML = `<img src="${e.target.result}" alt="Preview" class="img-fluid">`;
//         } else if (file.type.startsWith('video/')) {
//           previewHTML = `<video controls class="img-fluid"><source src="${e.target.result}" type="${file.type}"></video>`;
//         } else {
//           previewHTML = `<div class="text-center p-3"><i class="fas fa-file fa-2x mb-2"></i><br>${file.name}</div>`;
//         }
        
//         previewContent.innerHTML = previewHTML;
//         filePreview.style.display = 'block';
//       };
      
//       reader.readAsDataURL(file);
//     }

//     async function sendMessage() {
//       const message = messageInput.value.trim();
      
//       if (!message && !selectedFile) return;

//       let messageData = {
//         user: DISPLAY_NAME,
//         userId: USER_ID,
//         timestamp: serverTimestamp(),
//         type: 'text'
//       };

//       if (selectedFile) {
//         // In a real app, you'd upload the file to Firebase Storage first
//         // For now, we'll just indicate it's a media message
//         messageData.message = message || `Shared ${selectedFile.type.startsWith('image/') ? 'an image' : 'a file'}`;
//         messageData.type = selectedFile.type.startsWith('image/') ? 'image' : 'file';
//         messageData.fileName = selectedFile.name;
//         // messageData.fileUrl = 'path-to-uploaded-file'; // This would be the actual file URL
//       } else {
//         messageData.message = message;
//       }

//       // Send message to Firebase
//       try {
//         await push(chatRef, messageData);
        
//         // Clear inputs
//         messageInput.value = '';
//         selectedFile = null;
//         fileInput.value = '';
//         filePreview.style.display = 'none';
//         updateCharCount();
        
//         // Remove typing indicator
//         remove(typingRef);
//       } catch (error) {
//         console.error('Error sending message:', error);
//         alert('Failed to send message. Please try again.');
//       }
//     }

//     function addMessageToChat(data, messageId) {
//       // Hide empty chat state
//       emptyChat.style.display = 'none';

//       const isOwn = data.userId === USER_ID;
//       const time = data.timestamp ? new Date(data.timestamp).toLocaleTimeString([], { 
//         hour: '2-digit', 
//         minute: '2-digit' 
//       }) : 'now';

//       const messageDiv = document.createElement('div');
//       messageDiv.className = `chat-message ${isOwn ? 'own' : ''}`;
//       messageDiv.dataset.messageId = messageId;

//       let messageContent = '';

//       if (data.type === 'poll') {
//         messageContent = createPollHTML(data, messageId);
//       } else if (data.type === 'image') {
//         messageContent = `
//           <div class="media-message">
//             <img src="${data.fileUrl || '/static/images/placeholder.jpg'}" alt="${data.fileName}" class="img-fluid">
//             ${data.message ? `<p class="mt-2 mb-0">${escapeHtml(data.message)}</p>` : ''}
//           </div>
//         `;
//       } else {
//         messageContent = escapeHtml(data.message);
//       }

//       messageDiv.innerHTML = `
//         ${!isOwn ? `
//           <div class="message-info">
//             <div class="member-avatar me-2">
//               ${data.user.charAt(0).toUpperCase()}
//             </div>
//             <strong>${escapeHtml(data.user)}</strong>
//             <span class="text-muted ms-1">${time}</span>
//           </div>
//         ` : `
//           <div class="message-info">
//             <span class="text-muted">${time}</span>
//             <strong class="ms-1">You</strong>
//           </div>
//         `}
//         <div class="message-bubble ${isOwn ? 'own' : 'other'}">
//           ${messageContent}
//         </div>
//         <div class="message-reactions" id="reactions-${messageId}"></div>
//       `;

//       // Add click handler for reactions (only on other's messages)
//       if (!isOwn) {
//         const bubble = messageDiv.querySelector('.message-bubble');
//         bubble.addEventListener('dblclick', () => showReactionOptions(messageId));
//       }

//       chatMessages.appendChild(messageDiv);
//       scrollToBottom();
//     }

//     function createPollHTML(data, messageId) {
//       const options = data.options || [];
//       const totalVotes = options.reduce((sum, opt) => sum + (opt.votes || 0), 0);

//       let optionsHTML = '';
//       options.forEach((option, index) => {
//         const votes = option.votes || 0;
//         const percentage = totalVotes > 0 ? Math.round((votes / totalVotes) * 100) : 0;
        
//         optionsHTML += `
//           <div class="poll-option" data-option-index="${index}" onclick="voteInPoll('${messageId}', ${index})">
//             <div class="d-flex justify-content-between align-items-center">
//               <span>${escapeHtml(option.text)}</span>
//               <span class="badge bg-primary">${votes}</span>
//             </div>
//             <div class="poll-progress" style="width: ${percentage}%"></div>
//           </div>
//         `;
//       });

//       return `
//         <div class="poll-container">
//           <div class="poll-question">${escapeHtml(data.question)}</div>
//           ${optionsHTML}
//           <div class="poll-stats">Total votes: ${totalVotes}</div>
//         </div>
//       `;
//     }

//     function showReactionOptions(messageId) {
//       const emojis = ['👍', '❤️', '😂', '😮', '😢', '🎉'];
//       const emoji = emojis[Math.floor(Math.random() * emojis.length)]; // Random for demo
      
//       // In a real app, you'd show a proper emoji picker
//       addReaction(messageId, emoji);
//     }

//     async function addReaction(messageId, emoji) {
//       try {
//         const reactionRef = ref(db, `clubs/${CLUB_ID}/reactions/${messageId}/${emoji}/${USER_ID}`);
//         await set(reactionRef, {
//           username: DISPLAY_NAME,
//           timestamp: serverTimestamp()
//         });
//       } catch (error) {
//         console.error('Error adding reaction:', error);
//       }
//     }

//     window.voteInPoll = async function(messageId, optionIndex) {
//       try {
//         const voteRef = ref(db, `clubs/${CLUB_ID}/polls/${messageId}/votes/${USER_ID}`);
//         await set(voteRef, {
//           option: optionIndex,
//           username: DISPLAY_NAME,
//           timestamp: serverTimestamp()
//         });
        
//         // Update the poll display
//         updatePollResults(messageId);
//       } catch (error) {
//         console.error('Error voting in poll:', error);
//       }
//     };

//     function updatePollResults(messageId) {
//       // Listen for poll vote updates
//       onValue(ref(db, `clubs/${CLUB_ID}/polls/${messageId}/votes`), (snapshot) => {
//         const votes = snapshot.val() || {};
//         const pollElement = document.querySelector(`[data-message-id="${messageId}"] .poll-container`);
        
//         if (pollElement) {
//           // Count votes for each option
//           const optionVotes = {};
//           Object.values(votes).forEach(vote => {
//             optionVotes[vote.option] = (optionVotes[vote.option] || 0) + 1;
//           });
          
//           // Update the display
//           const options = pollElement.querySelectorAll('.poll-option');
//           const totalVotes = Object.values(optionVotes).reduce((sum, count) => sum + count, 0);
          
//           options.forEach((option, index) => {
//             const voteCount = optionVotes[index] || 0;
//             const percentage = totalVotes > 0 ? Math.round((voteCount / totalVotes) * 100) : 0;
            
//             const badge = option.querySelector('.badge');
//             const progress = option.querySelector('.poll-progress');
            
//             if (badge) badge.textContent = voteCount;
//             if (progress) progress.style.width = `${percentage}%`;
            
//             // Mark if user voted for this option
//             const userVote = votes[USER_ID];
//             if (userVote && userVote.option === index) {
//               option.classList.add('voted');
//             }
//           });
          
//           // Update total
//           const statsElement = pollElement.querySelector('.poll-stats');
//           if (statsElement) {
//             statsElement.textContent = `Total votes: ${totalVotes}`;
//           }
//         }
//       });
//     }

//     function setupPollModal() {
//       const addOptionBtn = document.getElementById('add-option');
//       const createPollBtn = document.getElementById('create-poll');
//       const pollForm = document.getElementById('poll-form');

//       addOptionBtn.addEventListener('click', function() {
//         const optionsContainer = document.getElementById('poll-options');
//         const currentOptions = optionsContainer.querySelectorAll('.option-row');
        
//         if (currentOptions.length >= 6) {
//           alert('Maximum 6 options allowed');
//           return;
//         }

//         const optionRow = document.createElement('div');
//         optionRow.className = 'mb-2 option-row';
//         optionRow.innerHTML = `
//           <div class="input-group">
//             <input type="text" class="form-control poll-option-input" placeholder="Option ${currentOptions.length + 1}" maxlength="100">
//             <button type="button" class="btn btn-outline-danger remove-option">
//               <i class="fas fa-times"></i>
//             </button>
//           </div>
//         `;

//         optionsContainer.appendChild(optionRow);
        
//         // Add remove handler
//         const removeBtn = optionRow.querySelector('.remove-option');
//         removeBtn.addEventListener('click', function() {
//           if (optionsContainer.querySelectorAll('.option-row').length > 2) {
//             optionRow.remove();
//             updateOptionPlaceholders();
//           }
//         });

//         updateOptionPlaceholders();
//       });

//       // Handle remove option buttons
//       document.addEventListener('click', function(e) {
//         if (e.target.closest('.remove-option')) {
//           const optionRow = e.target.closest('.option-row');
//           const optionsContainer = document.getElementById('poll-options');
          
//           if (optionsContainer.querySelectorAll('.option-row').length > 2) {
//             optionRow.remove();
//             updateOptionPlaceholders();
//           }
//         }
//       });

//       createPollBtn.addEventListener('click', async function() {
//         const question = document.getElementById('poll-question').value.trim();
//         const optionInputs = document.querySelectorAll('.poll-option-input');
        
//         if (!question) {
//           alert('Please enter a poll question');
//           return;
//         }

//         const options = [];
//         optionInputs.forEach(input => {
//           const value = input.value.trim();
//           if (value) options.push({ text: value, votes: 0 });
//         });

//         if (options.length < 2) {
//           alert('Please enter at least 2 options');
//           return;
//         }

//         try {
//           const pollData = {
//             user: DISPLAY_NAME,
//             userId: USER_ID,
//             type: 'poll',
//             question: question,
//             options: options,
//             timestamp: serverTimestamp()
//           };

//           await push(chatRef, pollData);
          
//           // Clear form
//           document.getElementById('poll-question').value = '';
//           optionInputs.forEach(input => input.value = '');
          
//           // Close modal
//           const modal = bootstrap.Modal.getInstance(document.getElementById('pollModal'));
//           modal.hide();
          
//         } catch (error) {
//           console.error('Error creating poll:', error);
//           alert('Failed to create poll. Please try again.');
//         }
//       });
//     }

//     function updateOptionPlaceholders() {
//       const optionInputs = document.querySelectorAll('.poll-option-input');
//       optionInputs.forEach((input, index) => {
//         input.placeholder = `Option ${index + 1}`;
//       });

//       // Update remove button states
//       const removeButtons = document.querySelectorAll('.remove-option');
//       removeButtons.forEach((btn, index) => {
//         btn.disabled = optionInputs.length <= 2;
//       });
//     }

//     function updateTypingIndicator(typingUsers) {
//       const currentlyTyping = Object.values(typingUsers).filter(user => 
//         user.typing && user.username !== DISPLAY_NAME && 
//         (Date.now() - user.timestamp < 5000) // 5 seconds timeout
//       );

//       if (currentlyTyping.length > 0) {
//         const names = currentlyTyping.map(user => user.username).slice(0, 3);
//         const text = names.length === 1 ? 
//           `${names[0]} is typing...` : 
//           `${names.join(', ')} are typing...`;
        
//         document.getElementById('typing-text').textContent = text;
//         typingIndicator.style.display = 'block';
//       } else {
//         typingIndicator.style.display = 'none';
//       }
//     }

//     function updateOnlineCount(onlineUsers) {
//       const count = Object.values(onlineUsers).filter(status => status === true).length;
//       document.getElementById('online-count').textContent = `${count} online`;
//     }

//     function updateOnlinePresence() {
//       // Set user as online
//       set(onlineRef, true);
      
//       // Set user as offline when they disconnect
//       onDisconnect(onlineRef).set(false);
      
//       // Cleanup typing when disconnecting
//       onDisconnect(typingRef).remove();
//     }

//     function scrollToBottom() {
//       chatMessages.scrollTop = chatMessages.scrollHeight;
//     }

//     function escapeHtml(text) {
//       const map = {
//         '&': '&amp;',
//         '<': '&lt;',
//         '>': '&gt;',
//         '"': '&quot;',
//         "'": '&#039;'
//       };
//       return text.replace(/[&<>"']/g, function(m) { return map[m]; });
//     }

//     // Share club function
//     window.shareClub = function() {
//       const clubUrl = window.location.origin + clubDetailUrl;
//       const shareText = `Check out this club: ${clubName} (${CLUB_ID})`;

//       if (navigator.share) {
//         navigator.share({
//           title: `${clubName} - ClubHub`,
//           text: shareText,
//           url: clubUrl
//         });
//       } else {
//         navigator.clipboard.writeText(clubUrl).then(() => {
//           alert('Club link copied to clipboard!');
//         });
//       }
//     };

//     // Load members for modal (placeholder)
//     document.getElementById('membersModal').addEventListener('show.bs.modal', function() {
//       // In a real app, you'd fetch this from your Django backend
//       const membersList = document.getElementById('members-list');
//       setTimeout(() => {
//         membersList.innerHTML = `
//           <div class="col-md-6 mb-3">
//             <div class="d-flex align-items-center">
//               <div class="member-avatar me-3">${DISPLAY_NAME.charAt(0)}</div>
//               <div>
//                 <h6 class="mb-0">${DISPLAY_NAME}</h6>
//                 <small class="text-muted">You</small>
//               </div>
//             </div>
//           </div>
//         `;
//       }, 1000);
//     });
