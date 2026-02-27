const jwt = require('jsonwebtoken');

/**
 * Middleware: verify session token issued after OTP verification.
 * Attaches decoded payload to req.session.
 */
function requireSession(req, res, next) {
  const token =
    req.headers['x-session-token'] ||
    req.body?.sessionToken ||
    req.query?.sessionToken;

  if (!token) {
    return res.status(401).json({ error: 'Session token required.' });
  }

  try {
    const decoded = jwt.verify(token, process.env.TOKEN_SECRET);
    req.session = decoded;
    next();
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Session expired. Please restart the application.' });
    }
    return res.status(401).json({ error: 'Invalid session token.' });
  }
}

module.exports = { requireSession };
