const express = require('express');
const session = require('express-session');
const multer = require('multer');
const fileRoutes = require('./routes/fileRoutes');

const app = express();

// Middleware setup
app.use(express.static('public')); // Serve static files
app.set('view engine', 'ejs'); // Set EJS as the template engine

// Configure session with a 10-minute expiration
app.use(session({
    secret: 'supersecretkey',
    resave: false,
    saveUninitialized: true,
    cookie: { maxAge: 10 * 60 * 1000 } // 10 minutes
}));

// File upload middleware setup (Multer)
const upload = multer({ dest: 'tmp/' });

// Routes setup
app.use('/', fileRoutes);

app.listen(3000, () => {
    console.log('Server is running on port 3000');
});
