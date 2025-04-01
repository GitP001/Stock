import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';

void main() {
  // Set transparent status bar
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );
  runApp(const NewsApp());
}

class NewsApp extends StatelessWidget {
  const NewsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'News App',
      theme: ThemeData.dark(),
      home: const NewsHomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

// API Configuration class for better URL management
class ApiConfig {
  // Base URL that automatically adjusts based on the platform
  static String get baseUrl {
    // When running in debug mode
    if (kDebugMode) {
      if (Platform.isAndroid) {
        // Android emulator needs this special IP to access host machine
        return 'http://10.0.2.2:5000/api';
      } else if (Platform.isIOS) {
        // iOS simulator can use localhost
        return 'http://localhost:5000/api';
      }
    }

    // For production or web
    return 'http://your-production-server.com/api';
  }

  // Endpoint for news
  static String get newsEndpoint => '$baseUrl/news';

  // Optional: Add other endpoints as needed
  static String get updateNewsEndpoint => '$baseUrl/news/update';
  static String get apiUsageEndpoint => '$baseUrl/news/api-usage';
}

// Simple NewsArticle model
class NewsArticle {
  final String id;
  final String imageUrl;
  final String title;
  final String summary;
  final String source;
  final String readTime;

  NewsArticle({
    required this.id,
    required this.imageUrl,
    required this.title,
    required this.summary,
    required this.source,
    required this.readTime,
  });
}

class NewsHomePage extends StatefulWidget {
  const NewsHomePage({super.key});

  @override
  State<NewsHomePage> createState() => _NewsHomePageState();
}

class _NewsHomePageState extends State<NewsHomePage> {
  int _selectedIndex = 0;
  final PageController _pageController = PageController();
  bool _isLoading = false;

  // Initially, two static articles for demonstration
  // We'll replace them with data from the backend
  List<NewsArticle> articles = [
    NewsArticle(
      id: '1',
      imageUrl: 'https://example.com/image1.jpg',
      title:
      'Two rings crafted from one billion-year-old natural diamond: Tanishq',
      summary:
      "This Valentine's Day, celebrate your eternal bond with the Soulmate Diamond Pair by Tanishq. Two rings crafted from one billion year-old-natural diamond, these rings symbolize an everlasting bond.",
      source: 'Tanishq',
      readTime: '2 min read',
    ),
    NewsArticle(
      id: '2',
      imageUrl: 'https://example.com/image2.jpg',
      title: 'Global Climate Summit Announces Breakthrough Agreement',
      summary:
      'World leaders reach historic consensus on ambitious climate action goals, setting new standards for environmental protection and sustainable development.',
      source: 'World News',
      readTime: '3 min read',
    ),
  ];

  @override
  void initState() {
    super.initState();
    // Attempt to fetch real articles from the backend
    _fetchArticlesFromBackend();
  }

  Future<void> _fetchArticlesFromBackend() async {
    // Avoid multiple simultaneous requests
    if (_isLoading) return;

    setState(() {
      _isLoading = true;
    });

    try {
      // Use timeout to avoid waiting forever
      final response = await http.get(Uri.parse(ApiConfig.newsEndpoint))
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);

        // Only update state if we actually got data and widget is still mounted
        if (data.isNotEmpty && mounted) {
          setState(() {
            articles = data.map((item) {
              return NewsArticle(
                id: item['id']?.toString() ?? '',
                imageUrl: item['image_url'] ??
                    'https://example.com/placeholder.jpg',
                title: item['title'] ?? 'No Title',
                summary: item['snippet'] ?? 'No Summary',
                source: item['source'] ?? 'Unknown Source',
                readTime: '2 min read', // Hard-coded or parse from item
              );
            }).toList();
          });
        }
      } else {
        print('Failed to load articles. Status code: ${response.statusCode}');
        if (mounted) {
          _showErrorSnackbar('Failed to load articles. Please try again later.');
        }
      }
    } catch (e) {
      print('Error fetching articles: $e');
      if (mounted) {
        _showErrorSnackbar('Network error. Please check your connection.');
      }
    } finally {
      // Always reset loading state
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  // Helper method to show errors to the user
  void _showErrorSnackbar(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          duration: const Duration(seconds: 3),
          action: SnackBarAction(
            label: 'Retry',
            onPressed: _fetchArticlesFromBackend,
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Main Content - Shorts/Reels style vertical PageView
          PageView.builder(
            controller: _pageController,
            scrollDirection: Axis.vertical,
            itemCount: articles.length,
            itemBuilder: (context, index) {
              return ArticleCard(article: articles[index]);
            },
            // Auto-load more content when approaching the end
            onPageChanged: (index) {
              // If we're near the end of the list, try to load more
              if (index >= articles.length - 2 && !_isLoading) {
                _fetchArticlesFromBackend();
              }
            },
          ),

          // Loading Indicator (only shows when loading more content)
          if (_isLoading)
            Positioned(
              top: 40,
              right: 20,
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                ),
              ),
            ),

          // Navigation Bar
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              height: 83,
              decoration: BoxDecoration(
                color: Colors.black,
                border: Border(
                  top: BorderSide(color: Colors.grey[900]!, width: 0.5),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavItem(0, Icons.home, 'Home'),
                  _buildNavItem(1, Icons.grid_view, 'Categories'),
                  _buildNavItem(2, Icons.person, 'Profile'),
                ],
              ),
            ),
          ),


        ],
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, String label) {
    return InkWell(
      onTap: () => setState(() => _selectedIndex = index),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: _selectedIndex == index ? Colors.white : Colors.grey,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: _selectedIndex == index ? Colors.white : Colors.grey,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class ArticleCard extends StatelessWidget {
  final NewsArticle article;

  const ArticleCard({super.key, required this.article});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 844,
      width: 390,
      color: Colors.black,
      child: Stack(
        children: [
          // Image Section
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: 380,
            child: Hero(
              tag: article.id,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  Image.network(
                    article.imageUrl,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) {
                      return Container(
                        color: Colors.grey[900],
                        child: const Icon(Icons.image, size: 50),
                      );
                    },
                  ),
                  Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.black.withOpacity(0.7),
                          Colors.transparent,
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Content Section
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            height: 464,
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Colors.black, Colors.grey[900]!],
                ),
              ),
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    article.title,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    article.summary,
                    style: const TextStyle(
                      fontSize: 18,
                      color: Colors.white70,
                      height: 1.5,
                    ),
                  ),
                  const Spacer(),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        article.source,
                        style: TextStyle(color: Colors.grey[400], fontSize: 14),
                      ),
                      Text(
                        article.readTime,
                        style: TextStyle(color: Colors.grey[400], fontSize: 14),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Interaction Buttons
          Positioned(
            right: 16,
            bottom: 120,
            child: Column(
              children: [
                _buildInteractionButton(Icons.share),
                const SizedBox(height: 16),
                _buildInteractionButton(Icons.bookmark_border),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInteractionButton(IconData icon) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        shape: BoxShape.circle,
      ),
      child: IconButton(
        icon: Icon(icon),
        color: Colors.white,
        onPressed: () {},
      ),
    );
  }
}