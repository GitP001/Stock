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
    if (kDebugMode) {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:5000/api';
      } else if (Platform.isIOS) {
        return 'http://localhost:5000/api';
      }
    }
    return 'http://your-production-server.com/api';
  }

  // Endpoints
  static String get newsEndpoint => '$baseUrl/news';
  static String get updateNewsEndpoint => '$baseUrl/news/update';
  static String get apiUsageEndpoint => '$baseUrl/news/api-usage';
}

// Simple NewsArticle model
class NewsArticle {
  final String id;
  final String imageUrl;
  final String title;
  final String originalTitle; // Added for reference
  final String summary;
  final String source;
  final String readTime;

  NewsArticle({
    required this.id,
    required this.imageUrl,
    required this.title,
    this.originalTitle = '', // Optional since it might not exist in older data
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
  // Replace with real data from backend
  List<NewsArticle> articles = [
    NewsArticle(
      id: '1',
      imageUrl: 'https://example.com/image1.jpg',
      title:
          'Two rings crafted from one billion-year-old natural diamond: Tanishq',
      summary:
          "This Valentine's Day, celebrate your eternal bond with the Soulmate Diamond Pair by Tanishq. Two rings crafted from one billion-year-old natural diamond, these rings symbolize an everlasting bond.",
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
    _fetchArticlesFromBackend();
  }

  // Add this to your NewsHomePage class
  Future<void> _refreshArticles() async {
    setState(() {
      _isLoading = true;
    });

    try {
      // Use the refresh parameter to force a fresh fetch
      final response = await http
          .get(Uri.parse(ApiConfig.newsEndpoint + "?refresh=true"))
          .timeout(const Duration(seconds: 10));

      // Process response as in _fetchArticlesFromBackend()
      // ...
    } catch (e) {
      // Handle errors
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  // Add this function to your Flutter app
  Future<void> _forceUpdateArticles() async {
    try {
      final response = await http
          .post(Uri.parse(ApiConfig.updateNewsEndpoint))
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        // Fetch the fresh articles
        _fetchArticlesFromBackend();
      }
    } catch (e) {
      print('Error updating articles: $e');
    }
  }

  Future<void> _fetchArticlesFromBackend() async {
    // Avoid multiple simultaneous requests
    if (_isLoading) return;

    setState(() {
      _isLoading = true;
    });

    try {
      // Use timeout to avoid waiting forever
      final response = await http
          .get(Uri.parse(ApiConfig.newsEndpoint))
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);

        // Only update state if we actually got data and widget is still mounted
        if (data.isNotEmpty && mounted) {
          setState(() {
            articles =
                data.map((item) {
                  return NewsArticle(
                    id: item['id']?.toString() ?? '',
                    imageUrl:
                        item['image_url'] ??
                        'https://example.com/placeholder.jpg',
                    title: item['title'] ?? 'No Title',
                    originalTitle:
                        item['original_title'] ?? item['title'] ?? 'No Title',
                    summary: item['snippet'] ?? 'No Summary',
                    source: item['source'] ?? 'Unknown Source',
                    readTime:
                        '${_calculateReadTime(item['snippet'] ?? '')} min read',
                  );
                }).toList();
          });
        }
      } else {
        print('Failed to load articles. Status code: ${response.statusCode}');
        if (mounted) {
          _showErrorSnackbar(
            'Failed to load articles. Please try again later.',
          );
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

  // Helper method to calculate read time based on word count
  String _calculateReadTime(String text) {
    // Average reading speed: 200-250 words per minute
    // Use 225 as a middle ground
    final wordCount = text.split(' ').length;
    final minutes = (wordCount / 225).ceil();
    return minutes.toString();
  }

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
          PageView.builder(
            controller: _pageController,
            scrollDirection: Axis.vertical,
            itemCount: articles.length,
            itemBuilder: (context, index) {
              return ArticleCard(article: articles[index]);
            },
            onPageChanged: (index) {
              if (index >= articles.length - 2 && !_isLoading) {
                _fetchArticlesFromBackend();
              }
            },
          ),
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
    // Check if there's a meaningful difference between original and enhanced titles
    final hasOriginalTitle =
        article.originalTitle.isNotEmpty &&
        article.originalTitle != article.title &&
        article.title.isNotEmpty; // Make sure the enhanced title is not empty

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
            height: MediaQuery.of(context).size.height * 0.35, // 35% of screen
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
            top: MediaQuery.of(context).size.height * 0.35,
            bottom: 0,
            left: 0,
            right: 0,
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
                  // Stock Symbols
                  // Display the title (enhanced if available, otherwise original)
                  // Use the title field which should contain the enhanced title
                  GestureDetector(
                    onLongPress:
                        hasOriginalTitle
                            ? () {
                              // Show original title on long press
                              final snackBar = SnackBar(
                                content: Text(
                                  "Original Title: ${article.originalTitle}",
                                  style: const TextStyle(color: Colors.white),
                                ),
                                backgroundColor: Colors.blueGrey[800],
                                duration: const Duration(seconds: 5),
                              );
                              ScaffoldMessenger.of(
                                context,
                              ).showSnackBar(snackBar);
                            }
                            : null,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Text(
                            // If the title is empty for some reason, use original title
                            article.title.isNotEmpty
                                ? article.title
                                : article.originalTitle,
                            style: const TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                        if (hasOriginalTitle)
                          Tooltip(
                            message: 'Long press to see original title',
                            child: Icon(
                              Icons.info_outline,
                              size: 16,
                              color: Colors.grey[400],
                            ),
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Summary with scroll capability
                  Expanded(
                    child: SingleChildScrollView(
                      child: Text(
                        article.summary,
                        style: const TextStyle(
                          fontSize: 18,
                          color: Colors.white70,
                          height: 1.5,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),
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
                const SizedBox(height: 16),
                // Read full article button
                _buildInteractionButton(Icons.article_outlined),
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
